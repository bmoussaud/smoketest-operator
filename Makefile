NAMESPACE=smoketest-operator
SOURCE_BRANCH=v0.0.1
VERSION="develop"
IMAGE_NAME=katapulted/smoketest-operator
IMAGE_VERSION=0.0.1
REGISTRY=harbor.mytanzu.xyz/library

IMAGE=$(IMAGE_NAME):$(IMAGE_VERSION)
BUILD_DATE=$(shell date)
GIT_REV=$(shell git rev-parse --short HEAD)


deploy: namespace
	kubectl apply -f crd -n $(NAMESPACE)
	kubectl api-resources --api-group katapult.org
	kubectl get deployments.apps -n $(NAMESPACE)
	
deploy-sample:	
	kubectl apply -f smoketest.yaml -n $(NAMESPACE)
	kubectl describe smoketests.katapult.org carvel-test  -n $(NAMESPACE)
	kubectl get smoketests.katapult.org -n $(NAMESPACE) carvel-test
	
	
undeploy-sample:
	kubectl patch smoketests.katapult.org carvel-test  -n $(NAMESPACE) -p '{"metadata": {"finalizers": []}}' --type merge
	kubectl delete -f smoketest.yaml -n $(NAMESPACE)
	
undeploy:
	kubectl delete -f crd -n $(NAMESPACE)
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
	

local-run: setup
	kopf run --log-format=full  smoketest-operator.py

setup:
	pip3 install --upgrade kopf 
	pip3 install --upgrade pykube-ng 
	pip3 install --upgrade stringcase 
	pip3 install --upgrade kubernetes
	
build-image:
	docker build --label org.label-schema.build-date="$(BUILD_DATE)" \
		--label org.label-schema.vcs-ref=$(GIT_REV) \
    	--label org.label-schema.vcs-url="https://github.com/bmoussaud/katapul/smoke" \
    	--label org.label-schema.version="$(SOURCE_BRANCH)" \
    	--label org.label-schema.schema-version="1.0" \
    	--build-arg VERSION="$(VERSION)" \
    	-f "." \
    	-t "$(IMAGE)"  \
		.	
push: build-image
	docker tag $(IMAGE) $(REGISTRY)/$(IMAGE)
	docker push $(REGISTRY)/$(IMAGE)

run-image: build-image 
	docker run --rm  -v ~/.kube:/home/operator/.kube $(IMAGE)

run-pushed-image: build-image push
	docker run --rm  -v ~/.kube:/home/operator/.kube $(REGISTRY)/$(IMAGE)