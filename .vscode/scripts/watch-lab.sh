#!/usr/bin/env bash

watch_lab() {
	cd packages/labextension
	npm run watch
}

watch_ndime() {
	cd packages/nbdime
	npm run watch
}

watch_lab & watch_ndime & jupyter lab --watch
