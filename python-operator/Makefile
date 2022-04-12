SOURCE_BRANCH=v0.0.1
VERSION="develop"
IMAGE_NAME=katapulted/smoketest-operator
IMAGE_VERSION=0.0.1
IMAGE=$(IMAGE_NAME):$(IMAGE_VERSION)

BUILD_DATE=$(shell date)
GIT_REV=$(shell git rev-parse --short HEAD)

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
    	-t "$(IMAGE_NAME)"  \
		.	