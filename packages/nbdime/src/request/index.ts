// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
'use strict';

import {
  JSONObject
} from '@phosphor/coreutils';

import {
  URLExt
} from '@jupyterlab/coreutils/lib/url';

import {
  ServerConnection
} from '@jupyterlab/services';


function urlRStrip(target: string): string {
  if (target.slice(-1) === '/') {
    return target.slice(0, -1);
  }
  return target;
}


export
function handleError(response: Response): Promise<Response> | Response {
  if (!response.ok) {
    if (response.status === 500 && response.body) {
      return response.text().then((body) => {
        throw new Error(body);
      });
    }
    throw new Error(`${response.status} ${response.statusText}`);
  }
  return response;
}


/**
 * Make a POST request passing a JSON argument and receiving a JSON result.
 */
export
function requestJsonPromise(url: string, argument: any): Promise<JSONObject> {
  let request = {
      method: 'POST',
      body: JSON.stringify(argument),
    };
  let settings = ServerConnection.makeSettings();
  return ServerConnection.makeRequest(url, request, settings)
    .then(handleError)
    .then((response) => {
      return response.json();
    });
}

/**
 * Make a POST request passing a JSON argument and receiving a JSON result.
 */
export
function requestJson(url: string, argument: any, callback: (result: any) => void, onError: (result: any) => void): void {
  let promise = requestJsonPromise(url, argument);
  promise.then((data) => {
    callback(data);
  }, (error: ServerConnection.NetworkError | ServerConnection.ResponseError) => {
    onError(error.message);
  });
}

/**
 * Make a diff request for the given base/remote specifiers (filenames)
 */
export
function requestDiffPromise(
    base: string, remote: string | undefined,
    baseUrl: string): Promise<JSONObject> {
  return requestJsonPromise(URLExt.join(window.location.origin, urlRStrip(baseUrl), 'api/diff'),
                            {base, remote});
}

/**
 * Make a diff request for the given base/remote specifiers (filenames)
 */
export
function requestDiff(
    base: string, remote: string | undefined,
    baseUrl: string,
    onComplete: (result: any) => void,
    onFail: (result: any) => void): void {
  requestJson(URLExt.join(window.location.origin, urlRStrip(baseUrl), 'api/diff'),
              {base, remote},
              onComplete,
              onFail);
}


/**
 * Make a diff request for the given base/remote specifiers (filenames)
 */
export
function requestMergePromise(
    base: string, local: string, remote: string,
    baseUrl: string): Promise<JSONObject> {
  return requestJsonPromise(URLExt.join(window.location.origin, urlRStrip(baseUrl), 'api/merge'),
              {base, local, remote});
}


/**
 * Make a diff request for the given base/remote specifiers (filenames)
 */
export
function requestMerge(
    base: string, local: string, remote: string,
    baseUrl: string,
    onComplete: (result: any) => void,
    onFail: (result: any) => void): void {
  requestJson(URLExt.join(window.location.origin, urlRStrip(baseUrl), 'api/merge'),
              {base, local, remote},
              onComplete,
              onFail);
}
