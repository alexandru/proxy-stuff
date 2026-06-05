IMAGE ?= ghcr.io/alexandru/proxy-stuff
TAG ?= latest
PLATFORMS ?= linux/amd64,linux/arm64
QNAP_PLATFORM ?= linux/amd64

.PHONY: test build build-qnap publish smoke-test require-image

test:
	python3 -m unittest discover -s tests

build:
	docker build -t api-proxy:local .

build-qnap:
	docker buildx build --platform $(QNAP_PLATFORM) -t api-proxy:qnap --load .

publish: require-image test
	docker buildx build --platform $(PLATFORMS) -t $(IMAGE):$(TAG) --push .

smoke-test:
	./scripts/local-smoke-test.sh

require-image:
	@if [ -z "$(IMAGE)" ]; then \
		echo "IMAGE is required, for example:"; \
		echo "  make publish IMAGE=ghcr.io/alexandru/proxy-stuff TAG=latest"; \
		exit 1; \
	fi
