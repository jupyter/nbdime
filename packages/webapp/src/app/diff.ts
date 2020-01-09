// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
'use strict';


import * as nbformat from '@jupyterlab/nbformat';

import {
  Panel, Widget
} from '@lumino/widgets';

import {
  RenderMimeRegistry
} from '@jupyterlab/rendermime';

import {
  defaultSanitizer
} from '@jupyterlab/apputils';

import {
  PageConfig
} from '@jupyterlab/coreutils';

import {
  MathJaxTypesetter
} from '@jupyterlab/mathjax2';

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
  getBaseUrl, getConfigOption, toggleSpinner, toggleShowUnchanged,
  markUnchangedRanges
} from './common';

import {
  exportDiff
} from './staticdiff';

import {
  rendererFactories
} from './rendermime';

let diffWidget: NotebookDiffWidget | null = null;

const prefixes = ['git:', 'checkpoint:'];

function hasPrefix(candidate: string): boolean {
  for (let p of prefixes) {
    if (candidate.slice(0, p.length) === p) {
      return true;
    }
  }
  return false;
}

function stripPrefix(s: string): string {
  for (let p of prefixes) {
    if (s.slice(0, p.length) === p) {
      return s.slice(p.length);
    }
  }
  return s;
}


/**
 * Show the diff as represented by the base notebook and a list of diff entries
 */
function showDiff(data: {base: nbformat.INotebookContent, diff: IDiffEntry[]}): Promise<void> {


  let rendermime = new RenderMimeRegistry({
    initialFactories: rendererFactories,
    sanitizer: defaultSanitizer,
    latexTypesetter: new MathJaxTypesetter({
      url: getConfigOption('mathjaxUrl'),
      config: getConfigOption('mathjaxConfig'),
    }),
  });

  let nbdModel = new NotebookDiffModel(data.base, data.diff);
  let nbdWidget = new NotebookDiffWidget(nbdModel, rendermime);

  let root = document.getElementById('nbdime-root');
  if (!root) {
    throw new Error('Missing root element "nbidme-root"');
  }
  root.innerHTML = '';
  // Hide unchanged cells by default:
  toggleShowUnchanged(!getConfigOption('hideUnchanged', true));

  let panel = new Panel();
  panel.id = 'main';
  Widget.attach(panel, root);
  panel.addWidget(nbdWidget);
  let work = nbdWidget.init();
  work.then(() => {
    window.onresize = () => { panel.update(); };
  });
  diffWidget = nbdWidget;
  return work;
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


function compare(base: string, remote: string | undefined, pushHistory: boolean | 'replace') {
  toggleSpinner(true);
  getDiff(base, remote);
  if (pushHistory) {
    let uri = window.location.pathname;
    base = stripPrefix(base);
    uri = '?base=' + encodeURIComponent(base);
    if (remote) {
      uri += '&remote=' + encodeURIComponent(remote);
    }
    editHistory(pushHistory, {base, remote},
      'Diff: "' + base + '" vs "' + remote + '"', uri);
  }
}

function editHistory(pushHistory: boolean | 'replace', statedata: any, title: string, url?: string): void {
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
function getDiff(base: string, remote: string | undefined) {
  let baseUrl = getBaseUrl();
  requestDiff(base, remote, baseUrl, onDiffRequestCompleted, onDiffRequestFailed);
}

/**
 * Callback for a successfull diff request
 */
function onDiffRequestCompleted(data: any) {
  let layoutWork = showDiff(data);

  layoutWork.then(() => {
    let exportBtn = document.getElementById('nbdime-export') as HTMLButtonElement;
    exportBtn.style.display = 'initial';
    toggleSpinner(false);
    markUnchangedRanges();
  });
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
  diffWidget = null;
  toggleSpinner(false);
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
 * Trust all outputs in diff
 */
function trustOutputs() {
  let trust = true;
  if (!diffWidget) {
    return;
  }
  let model = diffWidget.model;
  for (let cell of model.cells) {
    if (!cell.outputs) {
      continue;
    }
    for (let output of cell.outputs) {
      output.trusted = trust;
    }
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


/**
 *
 */
export
function initializeDiff() {
  attachToForm();
  // If arguments supplied in config, run diff directly:
  let base = getConfigOption('base');
  let remote = getConfigOption('remote');
  if (base && (remote || hasPrefix(base))) {
    compare(base, remote, 'replace');
  }

  let exportBtn = document.getElementById('nbdime-export') as HTMLButtonElement;
  exportBtn.onclick = exportDiff;

  let hideUnchangedChk = document.getElementById('nbdime-hide-unchanged') as HTMLInputElement;
  hideUnchangedChk.checked = getConfigOption('hideUnchanged', true);
  hideUnchangedChk.onchange = () => {
    toggleShowUnchanged(!hideUnchangedChk.checked, diffWidget);
  };

  let trustBtn = document.getElementById('nbdime-trust') as HTMLButtonElement;
  trustBtn.onclick = trustOutputs;
  trustBtn.style.display = 'initial';
}
