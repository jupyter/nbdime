// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
'use strict';


import {
  nbformat
} from 'jupyterlab/lib/notebook/notebook/nbformat';

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
  NotebookMergeModel
} from 'nbdime/lib/merge/model';

import {
  IMergeDecision
} from 'nbdime/lib/merge/decisions';

import {
  NotebookMergeWidget
} from 'nbdime/lib/merge/widget';



/**
 * Extract the merged notebook from the model, as well as any remaining
 * conflicts, and send them to the server for storage / further processing.
 */
export
function extractMergedNotebook(widget: NotebookMergeWidget): nbformat.INotebookContent {
  let nb = widget.model.serialize();
  let validated = widget.validateMerged(nb);
  if (JSON.stringify(nb) !== JSON.stringify(validated)) {
    alertify.error('Value in internal model did not correspond to value from editors. ' +
      'The values in the editors were used, but you should double check the output.');
  }
  return nb;
}
