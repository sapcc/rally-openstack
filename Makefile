IMAGE         := hub.global.cloud.sap/monsoon/rally-openstack
IMAGE_VERSION := 0.0.2

### Executables
DOCKER := docker

.PHONY: all
all: build push

.PHONY: build
build:
  $(DOCKER) build -t $(IMAGE):manila-$(IMAGE_VERSION) --rm \
  --build-arg CACHEBUST=$(date +%s) \
  .

.PHONY: push
push:
  $(DOCKER) push $(IMAGE):manila-$(IMAGE_VERSION)
