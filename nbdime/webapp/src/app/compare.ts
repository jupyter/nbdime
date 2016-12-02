// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
'use strict';


import {
  getDiff
} from './diff';

import {
  getMerge, closeMerge, saveMerged
} from './merge';

import {
  getConfigOption, closeTool
} from './common';


const ERROR_COMPARE_NUMBER = 'Need two or more values to compare!';

let hasMerge = false;

/**
 *
 */
export
function closeCompare(ev: Event, unloading?: boolean) {
  if (hasMerge) {
    return closeMerge(ev, unloading);
  } else {
    return closeTool();
  }
}

/**
 * Compare form submission callback. Sends a request for a
 * diff/merge to the server based on the content of the form.
 */
function onCompare(e: Event) {
  e.preventDefault();
  let b = (document.getElementById('compare-base') as HTMLInputElement).value;
  let c = (document.getElementById('compare-local') as HTMLInputElement).value;
  let r = (document.getElementById('compare-remote') as HTMLInputElement).value;
  compare(b, c, r, true);
  return false;
};

function compare(b: string, c: string, r: string, pushHistory: boolean | 'replace') {
  let count = 0;
  for (let v of [b, c, r]) {
    if (v) {
      count += 1;
    }
  }
  if (b && c && r) {
    // All values present, do merge
    getMerge(b, c, r);
    if (pushHistory) {
      let uri = window.location.pathname;
      uri += '?base=' + encodeURIComponent(b) +
        '&local=' + encodeURIComponent(c) +
        '&remote=' + encodeURIComponent(r);
      editHistory(pushHistory, {base: b, local: c, remote: r},
        'Merge: "' + c + '" - "' + b + '" - "' + r + '"', uri);
    }
    hasMerge = true;
  } else if (count < 2) {
    throw new Error(ERROR_COMPARE_NUMBER);
  } else {
    // Two values, figure out which
    let base: string;
    let remote: string;
    if (b) {
      base = b;
      if (c) {
        remote = c;
      } else {
        remote = r;
      }
    } else {
      base = c;
      remote = r;
    }
    getDiff(base, remote);
    if (pushHistory) {
      let uri = '/?base=' + encodeURIComponent(b) +
        '&local=' + encodeURIComponent(c) +
        '&remote=' + encodeURIComponent(r);
      editHistory(pushHistory, {base, remote},
        'Diff: "' + b + '" vs "' + r + '"', uri);
    }
    hasMerge = false;
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
 * Called when a 'back' is requested
 */
function onPopState(e: PopStateEvent) {
  if (e.state) {
    let eb = (document.getElementById('compare-base') as HTMLInputElement);
    let el = (document.getElementById('compare-local') as HTMLInputElement);
    let er = (document.getElementById('compare-remote') as HTMLInputElement);

    let base: string = e.state.base || '';
    let local: string = e.state.local || '';
    let remote: string = e.state.remote || '';

    eb.value = base;
    el.value = local;
    er.value = remote;
    compare(base, local, remote, false);
  }
}

/**
 * Wire up callbacks.
 */
function attachToForm() {
  let frm = document.getElementById('nbdime-compare-form') as HTMLFormElement;
  if (frm) {
    frm.onsubmit = onCompare;
    // It only makes sense to listen to pop state events when the form is
    // availalbe (i.e. when we are not a diff/mergetool):
    window.onpopstate = onPopState;
  }
}

/** */
export
function initializeCompare() {
  attachToForm();
  // If arguments supplied in config, run compare directly:
  let base = getConfigOption('base');
  let local = getConfigOption('local');
  let remote = getConfigOption('remote');
  try {
    compare(base, local, remote, false);
  } catch (e) {
    if (!(e instanceof Error && e.message === ERROR_COMPARE_NUMBER)) {
      throw e;
    }
  }
  let saveBtn = document.getElementById('nbdime-save') as HTMLButtonElement;
  if (saveBtn) {
    saveBtn.onclick = saveMerged;
  }
}
