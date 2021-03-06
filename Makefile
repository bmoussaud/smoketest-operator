APP:=smoketest-operator
APP_VERSION := 0.2.0-dev
APP_IMAGE  := ghcr.io/bmoussaud/$(APP)
PKG_IMAGE := ghcr.io/bmoussaud/$(APP)-package
REPO_IMAGE := ghcr.io/bmoussaud/$(APP)-repo

NAMESPACE=smoketest-operator

BUILD_DATE := $(shell date +"%Y-%m-%dT%TZ")
GIT_REV=$(shell git rev-parse --short HEAD)
CARVEL_BINARIES := ytt kbld imgpkg kapp

deploy: 
#kubectl create clusterrolebinding cluster-system-anonymous --clusterrole=cluster-admin --user=system:anonymous
	ytt -f config | kubectl apply -f-
	kubectl api-resources --api-group katapult.org
	kubectl get deployments.apps -n $(NAMESPACE)
	kubectl delete deployments.apps smoketest-operator -n $(NAMESPACE)
	
deploy-sample:	
	kubectl apply -f smoketest.yaml -n $(NAMESPACE)
	kubectl describe smoketests.katapult.org carvel-test  -n $(NAMESPACE)
	kubectl get smoketests.katapult.org -n $(NAMESPACE) carvel-test
	
undeploy-sample:
	kubectl patch smoketests.katapult.org carvel-test  -n $(NAMESPACE) -p '{"metadata": {"finalizers": []}}' --type merge
	kubectl delete -f smoketest.yaml -n $(NAMESPACE)
	
undeploy:
	ytt -f config | kubectl delete -f-
	kubectl api-resources --api-group katapult.org

namespace:
	kubectl create namespace $(NAMESPACE) --dry-run=client -o yaml | kubectl apply -f -
	kubectl get namespace $(NAMESPACE) 


# https://craignewtondev.medium.com/how-to-fix-kubernetes-namespace-deleting-stuck-in-terminating-state-5ed75792647e
force-delete-ns:
	kubectl get namespace $(NAMESPACE) -o json > /tmp/smok.json
	cat /tmp/smok.json | grep -v '"kubernetes' > /tmp/smoked.json
	kubectl replace --raw "/api/v1/namespaces/$(NAMESPACE)/finalize" -f /tmp/smoked.json
	kubectl delete ns $(NAMESPACE)
	

local-run: 
	kopf run --log-format=full  smoketest-operator.py

setup: 
	pip3 install --upgrade kopf 
	pip3 install --upgrade stringcase 
	pip3 install --upgrade kubernetes

clean:
	rm -rf target pkg/.imgpkg pkg/config pkg/package.yaml repo
	
build-image:
	ytt -f package.tpl.yaml -v app.version=$(APP_VERSION) -v "releaseDate=$(BUILD_DATE)" > pkg/package.yaml	
	rm -rf pkg/config pkg/.imgpkg && cp -a config pkg && cat config/values.yaml | sed "s/VERSION: latest/VERSION: ${APP_VERSION}/" > pkg/config/values.yaml
	@printf "`tput bold`= Build Image ${APP_IMAGE}`tput sgr0`\n"	
	docker build --label org.label-schema.build-date="$(BUILD_DATE)" \
		--label org.label-schema.vcs-ref=$(GIT_REV) \
    	--label org.label-schema.vcs-url="https://github.com/bmoussaud/smoketest-operator" \
    	--label org.label-schema.version="$(APP_VERSION)" \
    	--label org.label-schema.schema-version="1.0" \
		--label org.opencontainers.image.source="https://github.com/bmoussaud/smoketest-operator" \
    	--build-arg VERSION="$(APP_VERSION)" \
    	-f Dockerfile \
    	-t "$(APP_IMAGE)"  \
		.	 
push-image: build-image
	@printf "`tput bold`= Push Image ${APP_IMAGE}:${APP_VERSION}`tput sgr0`\n"	
	docker tag $(APP_IMAGE) $(APP_IMAGE):$(APP_VERSION)
	docker push $(APP_IMAGE):$(APP_VERSION)

run-image: build-image 
	docker run -i --rm  -v ~/.kube:/home/operator/.kube $(APP_IMAGE)

check-carvel:
	$(foreach exec,$(CARVEL_BINARIES),\
		$(if $(shell which $(exec)),,$(error "'$(exec)' not found. Carvel toolset is required. See instructions at https://carvel.dev/#install")))

push: check-carvel build-image push-image # Push packages.	
	@printf "`tput bold`= Generate the PKG Image ${PKG_IMAGE} $@`tput sgr0`\n"	
	mkdir pkg/.imgpkg && ytt -f pkg/config | kbld -f- --imgpkg-lock-output pkg/.imgpkg/images.yml && \
		imgpkg push --bundle ${PKG_IMAGE}:${APP_VERSION} --file pkg
	
	@printf "`tput bold`= Generate the REPO Image ${REPO_IMAGE} $@`tput sgr0`\n"	
	rm -rf repo && mkdir -p repo/packages && ytt -f pkg/package.yaml -f pkg/metadata.yaml -v app.version=${APP_VERSION} -v "releaseDate=${BUILD_DATE}" | kbld -f- -f pkg/.imgpkg/images.yml > repo/packages/packages.yaml
	rm -rf repo/.imgpkg && mkdir repo/.imgpkg && kbld -f repo/packages --imgpkg-lock-output repo/.imgpkg/images.yml && \
		imgpkg push --bundle ${REPO_IMAGE}:latest --file repo


deploy-package:
	tanzu package repository add smoketest-operator-repo --url ghcr.io/bmoussaud/smoketest-operator-repo:latest -n tanzu-package-repo-global 
	tanzu package repository list -n tanzu-package-repo-global
	tanzu package repository get smoketest-operator-repo -n tanzu-package-repo-global
	tanzu package available list smoketest-operator.bmoussaud.github.com -n tanzu-package-repo-global
	tanzu package install smoketest-operator --package-name smoketest-operator.bmoussaud.github.com --version 0.2.0-dev  -n tanzu-package-repo-global -f my-values.yaml

undeploy-package:
	tanzu package installed delete smoketest-operator -n tanzu-package-repo-global -y
	tanzu package repository delete smoketest-operator-repo -n tanzu-package-repo-global -y