#!/usr/bin/env bash


watch_ndime() {
	cd packages/nbdime
	npm run watch
}

watch_webapp() {
	cd packages/webapp
	npm run watch
}

watch_ndime & watch_webapp
