// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
'use strict';



/**
 * Make a POST request passing a JSON argument and receiving a JSON result.
 */
export
function requestJson(url: string, argument: any, callback: (result: any) => void, onError: (result: any) => void) {
  let xhttp = new XMLHttpRequest();
  xhttp.onreadystatechange = function() {
    if (xhttp.readyState === 4) {
      if (xhttp.status === 200) {
        let result: string = '';
        if (xhttp.responseText.length > 0) {
          result = JSON.parse(xhttp.responseText);
        }
        callback(result);
      } else {
        onError(xhttp.responseText);
      }
    }
  };
  xhttp.open('POST', url, true);
  xhttp.setRequestHeader('Content-type', 'application/json');
  xhttp.send(JSON.stringify(argument));
}

/**
 * Make a diff request for the given base/remote specifiers (filenames)
 */
export
function requestDiff(
    base: string, remote: string,
    onComplete: (result: any) => void,
    onFail: (result: any) => void) {
  requestJson('/api/diff',
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
    onComplete: (result: any) => void,
    onFail: (result: any) => void) {
  requestJson('/api/merge',
              {base, local, remote},
              onComplete,
              onFail);
}
