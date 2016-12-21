// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
'use strict';


import {
  nbformat
} from '@jupyterlab/services';

import {
  RenderMime
} from 'jupyterlab/lib/rendermime';

import {
  HTMLRenderer, LatexRenderer, ImageRenderer, TextRenderer,
  JavascriptRenderer, SVGRenderer, MarkdownRenderer
} from 'jupyterlab/lib/renderers';

import {
  defaultSanitizer
} from 'jupyterlab/lib/sanitizer';

import {
  Widget
} from 'phosphor/lib/ui/widget';

import {
  Panel
} from 'phosphor/lib/ui/panel';

import {
  IDiffEntry
} from 'nbdime/lib/diff/diffentries';

import {
  NotebookDiffModel
} from 'nbdime/lib/diff/model';

import {
  NotebookDiffWidget
} from 'nbdime/lib/diff/widget';

import {
  requestDiff
} from 'nbdime/lib/request';

import {
  getConfigOption
} from './common';


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

  let renderers: RenderMime.MimeMap<RenderMime.IRenderer> = {};
  let order: string[] = [];
  for (let t of transformers) {
    for (let m of t.mimetypes) {
      renderers[m] = t;
      order.push(m);
    }
  }
  let rendermime = new RenderMime({
    renderers: renderers, order: order, sanitizer: defaultSanitizer});

  let nbdModel = new NotebookDiffModel(data.base, data.diff);
  let nbdWidget = new NotebookDiffWidget(nbdModel, rendermime);

  let root = document.getElementById('nbdime-root');
  if (!root) {
    throw new Error('Missing root element "nbidme-root"');
  }
  root.innerHTML = '';
  let panel = new Panel();
  panel.id = 'main';
  Widget.attach(panel, root);
  panel.addWidget(nbdWidget);
  let work = nbdWidget.init();
  work.then(() => {
    window.onresize = () => { panel.update(); };
  });
}

/**
 * Diff form submission callback. Sends a request for a diff to the server based
 * on the content of the form.
 */
function onDiff(e: Event) {
  e.preventDefault();
  let b = (document.getElementById('diff-base') as HTMLInputElement).value;
  let r = (document.getElementById('diff-remote') as HTMLInputElement).value;
  compare(b, r, true);
  return false;
};


function compare(base: string, remote: string, pushHistory: boolean | 'replace') {
  getDiff(base, remote);
  if (pushHistory) {
    let uri = window.location.pathname;
    uri = '?base=' + encodeURIComponent(base) +
      '&remote=' + encodeURIComponent(remote);
    editHistory(pushHistory, {base, remote},
      'Diff: "' + base + '" vs "' + remote + '"', uri);
  }
}

function editHistory(pushHistory: boolean | 'replace', statedata: any, title?: string, url?: string): void {
  if (pushHistory === true) {
    history.pushState(statedata, title, url);
  } else if (pushHistory === 'replace') {
    history.replaceState(statedata, title, url);
  }
}


/**
 * Calls `requestDiff` with our response handlers
 */
export
function getDiff(base: string, remote: string) {
  requestDiff(base, remote, onDiffRequestCompleted, onDiffRequestFailed);
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
function onDiffRequestFailed(response: string) {
  console.log('Diff request failed.');
  let root = document.getElementById('nbdime-root');
  if (!root) {
    throw new Error('Missing root element "nbidme-root"');
  }
  root.innerHTML = '<pre>' + response + '</pre>';
}


/**
 * Called when a 'back' is requested
 */
function onPopState(e: PopStateEvent) {
  if (e.state) {
    let eb = (document.getElementById('diff-base') as HTMLInputElement);
    let er = (document.getElementById('diff-remote') as HTMLInputElement);
    eb.value = e.state.base;
    er.value = e.state.remote;
    compare(e.state.base, e.state.remote, false);
  }
}


/**
 * Wire up callbacks.
 */
function attachToForm() {
  let frm = document.getElementById('nbdime-diff-form') as HTMLFormElement;
  if (frm) {
    frm.onsubmit = onDiff;
    // It only makes sense to listen to pop state events when the form is
    // availalbe (i.e. when we are not a diff/mergetool):
    window.onpopstate = onPopState;
  }
}

/** */
export
function initializeDiff() {
  attachToForm();
  // If arguments supplied in config, run diff directly:
  let base = getConfigOption('base');
  let remote = getConfigOption('remote');
  if (base && remote) {
    compare(base, remote, 'replace');
  }
}
