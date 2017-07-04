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

/**
 * Make a POST request passing a JSON argument and receiving a JSON result.
 */
export
function requestJsonPromise(url: string, argument: any): Promise<JSONObject> {
  let request = {
      url: url,
      method: 'POST',
      data: JSON.stringify(argument),
    };
  let settings = ServerConnection.makeSettings();
  return ServerConnection.makeRequest(request, settings).then((response) => {
      return response.data;
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
  }, (error: ServerConnection.IError) => {
    onError(error.xhr.responseText);
  });
}

/**
 * Make a diff request for the given base/remote specifiers (filenames)
 */
export
function requestDiffPromise(
    base: string, remote: string | undefined,
    baseUrl: string): Promise<JSONObject> {
  return requestJsonPromise(URLExt.join(urlRStrip(baseUrl), 'api/diff'),
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
  requestJson(URLExt.join(urlRStrip(baseUrl), 'api/diff'),
              {base, remote},
              onComplete,
              onFail);
}


/**
 * Make a diff request for the given base/remote specifiers (filenames)
 */
export
function requestMergePrmise(
    base: string, local: string, remote: string,
    baseUrl: string): Promise<JSONObject> {
  return requestJsonPromise(URLExt.join(urlRStrip(baseUrl), 'api/merge'),
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
  requestJson(URLExt.join(urlRStrip(baseUrl), 'api/merge'),
              {base, local, remote},
              onComplete,
              onFail);
}
