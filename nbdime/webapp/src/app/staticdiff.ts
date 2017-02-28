// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
'use strict';

import {
  saveAs
} from 'file-saver';

import {
  EditorWidget
} from 'nbdime/lib/common/editor';



const collapsiblePanelExportJS =
`<script>
var headers = document.getElementsByClassName("jp-CollapsiblePanel-header");
for (var i=0;i<headers.length;++i){
  var header=headers[i];
  var slider = header.parentNode.getElementsByClassName("jp-CollapsiblePanel-slider")[0];
  header.onclick = function(slider){ return function() {
    if (slider.className.indexOf("opened") !== -1) {
      slider.className = slider.className.replace(/opened/g, "closed");
    } else {
      slider.className = slider.className.replace(/closed/g, "opened");
    }
  }; }(slider);
}
</script>`;

const codeMirrorEllipsisExportStyle =
`<style type="text/css">
.jp-Notebook-diff .CodeMirror-merge-collapsed-widget {
  cursor: initial;
}

.CodeMirror-gutters {
  height: auto !important;
}

.CodeMirror-sizer, .CodeMirror-scroll {
  margin-bottom: 0 !important;
  padding-bottom: 0 !important;
  margin-right: 0 !important;
  padding-right: 0 !important;
}

.CodeMirror-hscrollbar, .CodeMirror-vscrollbar,
.CodeMirror-merge-scrolllock, .CodeMirror-sizer + div {
  display: none !important;
}

.CodeMirror-scroll {
  overflow: auto !important;
}
</style>`;


function ensureRendered(callback: () => void): void {
  for (let e of EditorWidget.editors) {
    e.setOption('viewportMargin', Infinity);
  }
  window.requestAnimationFrame(() => {
    // Assume entire viewport has been rendered now
    callback();
    for (let e of EditorWidget.editors) {
      // Reset to default according to docs
      e.setOption('viewportMargin', 10);
    }
  });
}


/**
 * Download diff as static HTML
 */
export
function exportDiff(): void {
  let prefix = '<!DOCTYPE html>\n<html>\n<head>';
  prefix += document.head.innerHTML;
  prefix += codeMirrorEllipsisExportStyle + '\n</head><body>';
  let postfix = collapsiblePanelExportJS + '\n</body></html>';

  ensureRendered(() => {
    let rootNode = document.getElementById('nbdime-root')!;
    let content = rootNode.outerHTML;
    // Strip hover text of CM ellipses
    content = content.replace(/title="Identical text collapsed. Click to expand."/g, '');
    let blob = new Blob([prefix + content + postfix], {type: 'text/html;charset=utf-8'});

    saveAs(blob, 'diff.html');
  });
}
