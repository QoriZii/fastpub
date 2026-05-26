.PHONY: setup setup-python setup-node render-video clean

setup: setup-python setup-node

setup-python:
	uv sync

setup-node:
	cd packages/remotion-video && npm install

render-video:
	@echo "Usage: fastpub render <analysis.json> -f video --image-provider xai"

clean:
	rm -rf packages/remotion-video/node_modules
