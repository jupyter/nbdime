// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
'use strict';

import type { JSONObject } from '@lumino/coreutils';

import { URLExt } from '@jupyterlab/coreutils/lib/url';

import { ServerConnection } from '@jupyterlab/services';

function urlRStrip(target: string): string {
  if (target.slice(-1) === '/') {
    return target.slice(0, -1);
  }
  return target;
}

export function handleError(response: Response): Promise<Response> {
  if (!response.ok) {
    if (response.status === 500 && response.body) {
      return response.text().then(body => {
        throw new Error(body);
      });
    }
    throw new Error(`${response.status} ${response.statusText}`);
  }
  return Promise.resolve(response);
}

/**
 * Make a request to an nbdime API.
 */
export function requestApiPromise(
  baseUrl: string,
  apiPath: string,
  argument: any,
): Promise<Response> {
  const url = URLExt.join(urlRStrip(baseUrl), apiPath);
  let request = {
    method: 'POST',
    body: JSON.stringify(argument),
  };
  let settings = ServerConnection.makeSettings();
  return ServerConnection.makeRequest(url, request, settings).then(handleError);
}

/**
 * Make a request to an nbdime API.
 */
export function requestApi(
  baseUrl: string,
  apiPath: string,
  argument: any,
  onComplete: (result: any) => void,
  onFail: (errorMessage: string) => void,
): void {
  requestApiPromise(baseUrl, apiPath, argument).then(
    onComplete,
    (error: ServerConnection.NetworkError | ServerConnection.ResponseError) => {
      onFail(error.message);
    },
  );
}

/**
 * Make a POST request passing a JSON argument and receiving a JSON result.
 */
export function requestApiJsonPromise(
  baseUrl: string,
  apiPath: string,
  argument: any,
): Promise<JSONObject> {
  return requestApiPromise(baseUrl, apiPath, argument).then(response => {
    return response.json();
  });
}

/**
 * Make a POST request passing a JSON argument and receiving a JSON result.
 */
export function requestApiJson(
  baseUrl: string,
  apiPath: string,
  argument: any,
  callback: (result: any) => void,
  onError: (errorMessage: string) => void,
): void {
  requestApiJsonPromise(baseUrl, apiPath, argument).then(
    callback,
    (error: ServerConnection.NetworkError | ServerConnection.ResponseError) => {
      onError(error.message);
    },
  );
}

/**
 * Make a diff request for the given base/remote specifiers (filenames)
 */
export function requestDiffPromise(
  base: string,
  remote: string | undefined,
  baseUrl: string,
): Promise<JSONObject> {
  return requestApiJsonPromise(baseUrl, 'api/diff', { base, remote });
}

/**
 * Make a diff request for the given base/remote specifiers (filenames)
 */
export function requestDiff(
  base: string,
  remote: string | undefined,
  baseUrl: string,
  onComplete: (result: any) => void,
  onFail: (errorMessage: string) => void,
): void {
  requestApiJson(baseUrl, 'api/diff', { base, remote }, onComplete, onFail);
}

/**
 * Make a diff request for the given base/remote specifiers (filenames)
 */
export function requestMergePromise(
  base: string,
  local: string,
  remote: string,
  baseUrl: string,
): Promise<JSONObject> {
  return requestApiJsonPromise(baseUrl, 'api/merge', { base, local, remote });
}

/**
 * Make a diff request for the given base/remote specifiers (filenames)
 */
export function requestMerge(
  base: string,
  local: string,
  remote: string,
  baseUrl: string,
  onComplete: (result: any) => void,
  onFail: (errorMessage: string) => void,
): void {
  requestApiJson(
    baseUrl,
    'api/merge',
    { base, local, remote },
    onComplete,
    onFail,
  );
}
