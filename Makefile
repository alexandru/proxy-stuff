IMAGE ?= ghcr.io/alexandru/proxy-stuff
TAG ?= latest
PLATFORMS ?= linux/amd64,linux/arm64
AMD64_PLATFORM ?= linux/amd64
PLATFORM ?= linux/amd64
ARCH ?= amd64

.PHONY: test build build-amd64 publish publish-platform publish-manifest smoke-test require-image

test:
	python3 -m unittest discover -s tests

build:
	docker build -t api-proxy:local .

build-amd64:
	docker buildx build --platform $(AMD64_PLATFORM) -t api-proxy:amd64 --load .

publish: require-image test
	docker buildx build --platform $(PLATFORMS) -t $(IMAGE):$(TAG) --push .

publish-platform: require-image test
	docker build --platform $(PLATFORM) -t $(IMAGE):$(TAG)-$(ARCH) .
	docker push $(IMAGE):$(TAG)-$(ARCH)

publish-manifest: require-image
	docker manifest create $(IMAGE):$(TAG) \
		$(IMAGE):$(TAG)-amd64 \
		$(IMAGE):$(TAG)-arm64
	docker manifest push $(IMAGE):$(TAG)

smoke-test:
	./scripts/local-smoke-test.sh

require-image:
	@if [ -z "$(IMAGE)" ]; then \
		echo "IMAGE is required, for example:"; \
		echo "  make publish IMAGE=ghcr.io/alexandru/proxy-stuff TAG=latest"; \
		exit 1; \
	fi
