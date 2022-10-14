// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
'use strict';
Object.defineProperty(exports, "__esModule", { value: true });
exports.requestMerge = exports.requestMergePromise = exports.requestDiff = exports.requestDiffPromise = exports.requestApiJson = exports.requestApiJsonPromise = exports.requestApi = exports.requestApiPromise = exports.handleError = void 0;
const url_1 = require("@jupyterlab/coreutils/lib/url");
const services_1 = require("@jupyterlab/services");
function urlRStrip(target) {
    if (target.slice(-1) === '/') {
        return target.slice(0, -1);
    }
    return target;
}
function handleError(response) {
    if (!response.ok) {
        if (response.status === 500 && response.body) {
            return response.text().then((body) => {
                throw new Error(body);
            });
        }
        throw new Error(`${response.status} ${response.statusText}`);
    }
    return Promise.resolve(response);
}
exports.handleError = handleError;
/**
 * Make a request to an nbdime API.
 */
function requestApiPromise(baseUrl, apiPath, argument) {
    const url = url_1.URLExt.join(urlRStrip(baseUrl), apiPath);
    let request = {
        method: 'POST',
        body: JSON.stringify(argument),
    };
    let settings = services_1.ServerConnection.makeSettings();
    return services_1.ServerConnection.makeRequest(url, request, settings)
        .then(handleError);
}
exports.requestApiPromise = requestApiPromise;
/**
 * Make a request to an nbdime API.
 */
function requestApi(baseUrl, apiPath, argument, onComplete, onFail) {
    requestApiPromise(baseUrl, apiPath, argument)
        .then(onComplete, (error) => {
        onFail(error.message);
    });
}
exports.requestApi = requestApi;
/**
 * Make a POST request passing a JSON argument and receiving a JSON result.
 */
function requestApiJsonPromise(baseUrl, apiPath, argument) {
    return requestApiPromise(baseUrl, apiPath, argument)
        .then((response) => {
        return response.json();
    });
}
exports.requestApiJsonPromise = requestApiJsonPromise;
/**
 * Make a POST request passing a JSON argument and receiving a JSON result.
 */
function requestApiJson(baseUrl, apiPath, argument, callback, onError) {
    requestApiJsonPromise(baseUrl, apiPath, argument)
        .then(callback, (error) => {
        onError(error.message);
    });
}
exports.requestApiJson = requestApiJson;
/**
 * Make a diff request for the given base/remote specifiers (filenames)
 */
function requestDiffPromise(base, remote, baseUrl) {
    return requestApiJsonPromise(baseUrl, 'api/diff', { base, remote });
}
exports.requestDiffPromise = requestDiffPromise;
/**
 * Make a diff request for the given base/remote specifiers (filenames)
 */
function requestDiff(base, remote, baseUrl, onComplete, onFail) {
    requestApiJson(baseUrl, 'api/diff', { base, remote }, onComplete, onFail);
}
exports.requestDiff = requestDiff;
/**
 * Make a diff request for the given base/remote specifiers (filenames)
 */
function requestMergePromise(base, local, remote, baseUrl) {
    return requestApiJsonPromise(baseUrl, 'api/merge', { base, local, remote });
}
exports.requestMergePromise = requestMergePromise;
/**
 * Make a diff request for the given base/remote specifiers (filenames)
 */
function requestMerge(base, local, remote, baseUrl, onComplete, onFail) {
    requestApiJson(baseUrl, 'api/merge', { base, local, remote }, onComplete, onFail);
}
exports.requestMerge = requestMerge;
//# sourceMappingURL=index.js.map