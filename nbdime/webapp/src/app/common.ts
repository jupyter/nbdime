// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
'use strict';

import 'codemirror/lib/codemirror.css';
import 'jupyterlab/lib/codemirror/index.css';
import 'nbdime/lib/styles/common.css';
import './common.css';

/**
 * Global config data for the Nbdime application.
 */
let configData: any = null;

/**
 *  Make an object fully immutable by freezing each object in it.
 */
function deepFreeze(obj: any): any {

  // Freeze properties before freezing self
  Object.getOwnPropertyNames(obj).forEach(function(name) {
    let prop = obj[name];

    // Freeze prop if it is an object
    if (typeof prop === 'object' && prop !== null && !Object.isFrozen(prop)) {
      deepFreeze(prop);
    }
  });

  // Freeze self
  return Object.freeze(obj);
}

/**
 * Retrive a config option
 */
export
function getConfigOption(name: string): any {
  if (configData) {
    return configData[name];
  }
  if (typeof document !== 'undefined') {
    let el = document.getElementById('nbdime-config-data');
    if (el) {
      configData = JSON.parse(el.textContent);
    } else {
      configData = {};
    }
  }
  configData = deepFreeze(configData);
  return configData[name];
}

/**
 * POSTs to the server that it should shut down if it was launched as a
 * difftool/mergetool.
 *
 * Used to indicate that the tool has finished its operation, and that the tool
 * should return to its caller.
 */
export
function closeTool(exitCode=0) {
  let xhttp = new XMLHttpRequest();
  let url = '/api/closetool';
  xhttp.open('POST', url, false);
  xhttp.setRequestHeader('exit_code', exitCode.toString());
  xhttp.send();
  window.close();
}

