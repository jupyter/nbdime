// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
'use strict';


import * as alertify from 'alertify.js';

import {
  nbformat
} from '@jupyterlab/coreutils';

import {
  Panel, Widget
} from '@phosphor/widgets';

import {
  RenderMime
} from '@jupyterlab/rendermime';

import {
  defaultSanitizer
} from '@jupyterlab/apputils';

import {
  NotebookMergeModel
} from 'nbdime/lib/merge/model';

import {
  IMergeDecision
} from 'nbdime/lib/merge/decisions';

import {
  NotebookMergeWidget
} from 'nbdime/lib/merge/widget';

import {
  stringify
} from 'nbdime/lib/patch';

import {
  requestMerge, requestJson
} from 'nbdime/lib/request';

import {
  getBaseUrl, getConfigOption, closeTool, toggleSpinner,
  toggleShowUnchanged, markUnchangedRanges
} from './common';

import {
  rendererFactories
} from './rendermime';

import {
  extractMergedNotebook
} from './save';


let mergeWidget: NotebookMergeWidget | null = null;

/**
 * Show the merge as represented by the base notebook and a
 * list of merge decisions
 */
function showMerge(data: {
    base: nbformat.INotebookContent,
    merge_decisions: IMergeDecision[]
    }): Promise<void> {

  let rendermime = new RenderMime({
    initialFactories: rendererFactories,
    sanitizer: defaultSanitizer,
  });

  let nbmModel = new NotebookMergeModel(data.base,
      data.merge_decisions);
  let nbmWidget = new NotebookMergeWidget(nbmModel, rendermime);

  let root = document.getElementById('nbdime-root');
  if (!root) {
    throw new Error('Missing root element "nbidme-root"');
  }
  root.innerHTML = '';
  let panel = new Panel();
  panel.id = 'main';
  Widget.attach(panel, root);
  panel.addWidget(nbmWidget);
  let work = nbmWidget.init();
  work.then(() => {
    window.onresize = () => { panel.update(); };
  });
  mergeWidget = nbmWidget;
  return work;
}

/**
 * Calls `requestMerge` with our response handlers
 */
export
function getMerge(base: string, local: string, remote: string) {
  let baseUrl = getBaseUrl();
  requestMerge(base, local, remote, baseUrl, onMergeRequestCompleted, onMergeRequestFailed);
}

/**
 * Merge form submission callback. Sends a request for a merge to the server
 * based on the content of the form.
 *
 * Also pushes state to history for navigation history wo/reload
 */
function onMerge(e: Event) {
  e.preventDefault();
  let b = (document.getElementById('merge-base') as HTMLInputElement).value;
  let c = (document.getElementById('merge-local') as HTMLInputElement).value;
  let r = (document.getElementById('merge-remote') as HTMLInputElement).value;
  compare(b, c, r, true);
  return false;
};

function compare(b: string, c: string, r: string, pushHistory: boolean | 'replace') {
  // All values present, do merge
  toggleSpinner(true);
  getMerge(b, c, r);
  if (pushHistory) {
    let uri = window.location.pathname;
    uri += '?base=' + encodeURIComponent(b) +
      '&local=' + encodeURIComponent(c) +
      '&remote=' + encodeURIComponent(r);
    editHistory(pushHistory, {base: b, local: c, remote: r},
      'Merge: "' + c + '" - "' + b + '" - "' + r + '"', uri);
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
 * Called when a 'back' is requested
 */
function onPopState(e: PopStateEvent) {
  if (e.state) {
    let eb = (document.getElementById('merge-base') as HTMLInputElement);
    let el = (document.getElementById('merge-local') as HTMLInputElement);
    let er = (document.getElementById('merge-remote') as HTMLInputElement);

    eb.value = e.state.base;
    el.value = e.state.local;
    er.value = e.state.remote;
    compare(e.state.base, e.state.local, e.state.remote, false);
  }
}

/**
 * Callback for a successfull merge request
 */
function onMergeRequestCompleted(data: any) {
  let layoutWork = showMerge(data);
  layoutWork.then(() => {
    toggleSpinner(false);
    markUnchangedRanges();
  });
}

/**
 * Callback for a failed merge request
 */
function onMergeRequestFailed(response: string) {
  console.log('Merge request failed.');
  let root = document.getElementById('nbdime-root');
  if (!root) {
    throw new Error('Missing root element "nbidme-root"');
  }
  root.innerHTML = '<pre>' + response + '</pre>';
  mergeWidget = null;
  toggleSpinner(false);
}


/**
 * Extract the merged notebook from the model, as well as any remaining
 * conflicts, and send them to the server for storage / further processing.
 */
export
function saveMerged() {
  if (!mergeWidget) {
    return;
  }
  let nb = extractMergedNotebook(mergeWidget);
  let conflicts: IMergeDecision[] = [];
  for (let md of mergeWidget.model.conflicts) {
    conflicts.push(md.serialize());
  }
  submitMerge(nb, conflicts);
}


function downloadNotebook(notebook: nbformat.INotebookContent, filename: string) {
  let element = document.createElement('a');
  element.setAttribute(
    'href', 'data:text/plain;charset=utf-8,' +
    encodeURIComponent(stringify(notebook)));
  element.setAttribute('download', filename);

  element.style.display = 'none';
  document.body.appendChild(element);
  try {
    element.click();
  } finally {
    document.body.removeChild(element);
  }
}


function getMergeFilename() {
  // If present use 'outputfilename'
  let filename = getConfigOption('outputfilename');
  // Otherwise use base name as suggestion
  if (!filename) {
    filename = getConfigOption('base');
  }
  // Fallback:
  if (!filename) {
    filename = 'merged.ipynb';
  }
  return filename;
}

/**
 *
 */
export
function downloadMerged() {
  if (!mergeWidget) {
    return;
  }
  function download() {
    let filename = getMergeFilename();
    let nb = extractMergedNotebook(mergeWidget!);
    downloadNotebook(nb, filename);
  }
  let conflicted = mergeWidget.model.conflicts.length > 0;
  if (conflicted) {
    alertify.confirm('There are conflicts remaining. ' +
      'Do you still want to download the merge output?', () => {
        download();
      });
  } else {
    download();
  }
}

/**
 * Submit a merged notebook
 */
function submitMerge(mergedNotebook: nbformat.INotebookContent,
                     conflicts: IMergeDecision[]) {
  requestJson('/api/store',
              {merged: mergedNotebook,
               conflicts: conflicts},
               onSubmissionCompleted,
               onSubmissionFailed);
}

/**
 * Callback for a successful store of the submitted merged notebook
 */
function onSubmissionCompleted() {
  alertify.success('Merged notebook saved successfully');
  mergeWidget!.model.unsavedChanges = false;
}

/**
 * Callback for a failed store of the submitted merged notebook
 */
function onSubmissionFailed(response: string) {
  alertify.error('Was not able to save the notebook! See console and/or server log for details.');
}


/**
 *
 */
export
function closeMerge(ev: Event, unloading=false): string | void | null {
  if (!mergeWidget) {
    return closeTool(1);
  }
  let savable = getConfigOption('savable');
  for (let md of mergeWidget.model.conflicts) {
    if (md.conflict) {
      if (mergeWidget.model.unsavedChanges && savable) {
        let prompt = 'There are remaining conflicts, and you have unsaved changes. Do you want to close anyway?';
        if (unloading) {
          ev.returnValue = true;
          return prompt;
        }
        alertify.confirm(prompt,
          () => {
            window.onbeforeunload = null!;
            closeTool(1);
          },
          () => {
            ev.preventDefault();
          });
        return null;
      } else {
        let prompt = 'There are remaining conflicts. Do you want to close anyway?';
        if (unloading) {
          ev.returnValue = true;
          return prompt;
        }
        alertify.confirm(prompt,
          () => {
            window.onbeforeunload = null!;
            closeTool(1);
          },
          () => {
            ev.preventDefault();
          });
        return null;
      }
    }
  }
  if (mergeWidget.model.unsavedChanges && savable) {
    let prompt = 'There are unsaved changes. Do you want to close anyway?';
    if (unloading) {
      ev.returnValue = true;
      return prompt;
    }
    alertify.confirm(prompt,
      () => {
        window.onbeforeunload = null!;
        closeTool(0);
      },
      () => {
        ev.preventDefault();
      });
    return null;
  }
  closeTool(0);
  return null;
}


/**
 * Wire up callbacks.
 */
function attachToForm() {
  let frm = document.getElementById('nbdime-merge-form') as HTMLFormElement;
  if (frm) {
    frm.onsubmit = onMerge;
    // It only makes sense to listen to pop state events when the form is
    // availalbe (i.e. when we are not a diff/mergetool):
    window.onpopstate = onPopState;
  }
}

/** */
export
function initializeMerge() {
  attachToForm();
  // If arguments supplied in config, run merge directly:
  let base = getConfigOption('base');
  let local = getConfigOption('local');  // Only available for merge
  let remote = getConfigOption('remote');
  if (base && local && remote) {
    compare(base, local, remote, 'replace');
  }

  let savable = getConfigOption('savable');
  let saveBtn = document.getElementById('nbdime-save') as HTMLButtonElement;
  if (savable) {
    saveBtn.onclick = saveMerged;
    saveBtn.style.display = 'initial';
  }
  let downloadBtn = document.getElementById('nbdime-download') as HTMLButtonElement;
  downloadBtn.onclick = downloadMerged;
  downloadBtn.style.display = 'initial';

  let hideUnchangedChk = document.getElementById('nbdime-hide-unchanged') as HTMLInputElement;
  hideUnchangedChk.onchange = () => {
    toggleShowUnchanged(!hideUnchangedChk.checked);
  };
}
