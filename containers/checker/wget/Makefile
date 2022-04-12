IMAGE_NAME=katapulted/checker-wget
IMAGE_VERSION=0.0.1
IMAGE=$(IMAGE_NAME):$(IMAGE_VERSION)
REGISTRY=localregistry:5000

build:
	SOURCE_BRANCH=v0.0.1 DOCKERFILE_PATH=. IMAGE_NAME=$(IMAGE) ./build.sh

push: build 
	docker tag $(IMAGE) $(REGISTRY)/$(IMAGE)
	docker push $(REGISTRY)/$(IMAGE)

dockerhub-push: build 	
	docker push  $(IMAGE)

docker-run: build
	docker run --rm -e EXPECTED_RESPONSE_TEXT="html" -e RETRY_INTERVAL_SECS=1 -e START_DELAY_SECS=1 -e URL=http://front.mytanzu.xyz/pets -e SHOW_PAGE_CONTENT=0   $(IMAGE) 
