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
  initializeCompare, closeCompare
} from './app/compare';

import {
  closeTool, getConfigOption, handleError
} from './app/common';


import 'codemirror/lib/codemirror.css';
import 'jupyterlab/lib/codemirror/index.css';

import 'phosphor/styles/base.css';
import 'jupyterlab/lib/basestyle/materialcolors.css';
import 'jupyterlab/lib/default-theme/variables.css';
import 'jupyterlab/lib/markdownwidget/index.css';
import 'jupyterlab/lib/notebook/index.css';
import 'jupyterlab/lib/renderers/index.css';
import 'jupyterlab/lib/editorwidget/index.css';
import 'jupyterlab/lib/editorwidget/index.css';

import 'nbdime/lib/common/collapsible.css';
import 'nbdime/lib/upstreaming/flexpanel.css';
import 'nbdime/lib/common/dragpanel.css';
import 'nbdime/lib/styles/variables.css';
import 'nbdime/lib/styles/common.css';
import 'nbdime/lib/styles/diff.css';
import 'nbdime/lib/styles/merge.css';

import './app/common.css';
import './app/diff.css';
import './app/merge.css';


/** */
function initialize() {
  let onclose = (ev) => { closeTool(); };
  if (document.getElementById('compare-local')) {
    initializeCompare();
    onclose = closeCompare;
  } else if (getConfigOption('local') || document.getElementById('merge-local')) {
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
