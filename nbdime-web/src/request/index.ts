// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
'use strict';

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
function requestJson(url: string, argument: any, callback: (result: any) => void, onError: (result: any) => void) {
  let request = {
      url: url,
      method: 'POST',
      data: JSON.stringify(argument),
    };
  let settings = ServerConnection.makeSettings({});
  let promise = ServerConnection.makeRequest(request, settings);

  promise.then((response) => {
    callback(response.data);
  }, (error: ServerConnection.IError) => {
    onError(error.xhr.responseText);
  });
}

/**
 * Make a diff request for the given base/remote specifiers (filenames)
 */
export
function requestDiff(
    base: string, remote: string,
    baseUrl: string,
    onComplete: (result: any) => void,
    onFail: (result: any) => void) {
  requestJson(URLExt.join(urlRStrip(baseUrl), 'api/diff'),
              {base, remote},
              onComplete,
              onFail);
}


/**
 * Make a diff request for the given base/remote specifiers (filenames)
 */
export
function requestMerge(
    base: string, local: string, remote: string,
    baseUrl: string,
    onComplete: (result: any) => void,
    onFail: (result: any) => void) {
  requestJson(URLExt.join(urlRStrip(baseUrl), 'api/merge'),
              {base, local, remote},
              onComplete,
              onFail);
}
