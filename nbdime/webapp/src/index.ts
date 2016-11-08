// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
'use strict';

import {
  initializeDiff
} from './app/diff';

import {
  initializeMerge, closeMerge
} from './app/merge';

import {
  closeTool, getConfigOption, handleError
} from './app/common';

/** */
function initialize() {
  let onclose = (ev) => { closeTool(); };
  if (getConfigOption('local') || document.getElementById('merge-local')) {
    initializeMerge();
    onclose = closeMerge;
  } else {
    initializeDiff();
  }

  let closable = getConfigOption('closable');
  let closeBtn = document.getElementById('nbdime-close') as HTMLButtonElement;
  if (closable) {
    closeBtn.onclick = onclose;
    window.onbeforeunload = onclose;
    closeBtn.style.display = 'initial';
  }
}

window.onload = initialize;
window.onerror = handleError;
