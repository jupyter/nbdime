// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
'use strict';


import {
  nbformat
} from 'jupyterlab/lib/notebook/notebook/nbformat';

import {
  RenderMime, MimeMap, IRenderer
} from 'jupyterlab/lib/rendermime';

import {
  HTMLRenderer, LatexRenderer, ImageRenderer, TextRenderer,
  JavascriptRenderer, SVGRenderer, MarkdownRenderer
} from 'jupyterlab/lib/renderers';

import {
  Widget
} from 'phosphor-widget';

import {
  Panel
} from 'phosphor-panel';

import {
  IDiffEntry
} from './diffutil';

import {
  NotebookDiffModel
} from './diffmodel';

import {
  NotebookDiffWidget
} from './widgets';

import 'jupyterlab/lib/index.css';
import 'jupyterlab/lib/theme.css';


/**
 * Show the diff as represented by the base notebook and a list of diff entries
 */
function showDiff(data: {base: nbformat.INotebookContent, diff: IDiffEntry[]}) {
  const transformers = [
    new JavascriptRenderer(),
    new MarkdownRenderer(),
    new HTMLRenderer(),
    new ImageRenderer(),
    new SVGRenderer(),
    new LatexRenderer(),
    new TextRenderer()
  ];

  let renderers: MimeMap<IRenderer<Widget>> = {};
  let order: string[] = [];
  for (let t of transformers) {
    for (let m of t.mimetypes) {
      renderers[m] = t;
      order.push(m);
    }
  }
  let rendermime = new RenderMime<Widget>(renderers, order);

  let nbdModel = new NotebookDiffModel(data.base, data.diff);
  let nbdWidget = new NotebookDiffWidget(nbdModel, rendermime);

  let root = document.getElementById('nbdime-root');
  root.innerHTML = '';
  let panel = new Panel();
  panel.id = 'main';
  panel.attach(root);
  panel.addChild(nbdWidget);
  window.onresize = () => { panel.update(); };
}

/**
 * Diff form submission callback. Sends a request for a diff to the server based
 * on the content of the form.
 */
function onDiff(e: Event) {
  e.preventDefault();
  var b = (document.getElementById('diff-base') as HTMLInputElement).value;
  var r = (document.getElementById('diff-remote') as HTMLInputElement).value;
  requestDiff(b, r);
  let uri = '/diff?base=' + encodeURIComponent(b) +
    '&remote=' + encodeURIComponent(r);
  history.pushState({base: b, remote: r},
    'Diff: "' + b + '" vs "' + r + '"', uri);
  return false;
};

/**
 * Called when a 'back' is requested
 */
function onPopState(e: PopStateEvent) {
  if (e.state) {
    var eb = (document.getElementById('diff-base') as HTMLInputElement);
    var er = (document.getElementById('diff-remote') as HTMLInputElement);
    eb.value = e.state.base;
    er.value = e.state.remote;
    requestDiff(e.state.base, e.state.remote);
  }
}

/**
 * Make a POST request passing a JSON argument and receiving a JSON result.
 */
function requestJson(url: string, argument: any, callback: any, onError: any) {
  var xhttp = new XMLHttpRequest();
  xhttp.onreadystatechange = function() {
    if (xhttp.readyState == 4) {
      if (xhttp.status == 200) {
        var result = JSON.parse(xhttp.responseText);
        callback(result);
      } else {
        onError();
      }
    }
  };
  xhttp.open('POST', url, true)
  xhttp.setRequestHeader('Content-type', 'application/json');
  xhttp.send(JSON.stringify(argument));
}

/**
 * Make a diff request for the given base/remote specifiers (filenames)
 */
function requestDiff(base: string, remote: string) {
  requestJson('/api/diff',
              {base:base, remote:remote},
              onDiffRequestCompleted,
              onDiffRequestFailed);
}

/**
 * Callback for a successfull diff request
 */
function onDiffRequestCompleted(data: any) {
  showDiff(data);
}

/**
 * Callback for a failed diff request
 */
function onDiffRequestFailed() {
  console.log('Diff request failed.');
}

/**
 * Global config data for the Nbdime application.
 */
var configData: any = null;

/**
 *  Make an object fully immutable by freezing each object in it.
 */
function deepFreeze(obj: any): any {

  // Freeze properties before freezing self
  Object.getOwnPropertyNames(obj).forEach(function(name) {
    var prop = obj[name];

    // Freeze prop if it is an object
    if (typeof prop == 'object' && prop !== null && !Object.isFrozen(prop)) {
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
function closeTool() {
  //TODO: Send an exit code
  var xhttp = new XMLHttpRequest();
  var url = '/api/closetool';
  xhttp.open('POST', url, false);
  xhttp.send();
  window.close();
}

/**
 * Wire up callbacks.
 */
function attachToForm() {
  var frm = document.getElementById('nbdime-diff-form') as HTMLFormElement;
  if (frm) {
    frm.onsubmit = onDiff;
    // It only makes sense to listen to pop state events when the form is
    // availalbe (i.e. when we are not a diff/mergetool):
    window.onpopstate = onPopState;
  }
}

/** */
function initialize() {
  attachToForm();
  // If arguments supplied in config, run diff directly:
  let base = getConfigOption('base');
  let remote = getConfigOption('remote');
  if (base && remote) {
    requestDiff(base, remote);
  }

  // If launched as a tool, there should be a close button, to indicate that
  // the tool has finshed. If present, wire it to events, and connect to
  // window unload event as well:
  let close_btn = document.getElementById('nbdime-close') as HTMLButtonElement;
  if (close_btn) {
    close_btn.onclick = closeTool;
    window.onbeforeunload = closeTool;
  }
}

window.onload = initialize;
