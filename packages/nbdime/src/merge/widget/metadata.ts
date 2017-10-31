// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
'use strict';

import {
  nbformat
} from '@jupyterlab/coreutils';

import {
  Panel
} from '@phosphor/widgets';

import {
  createNbdimeMergeView, MergeView
} from '../../common/mergeview';

import {
  CollapsiblePanel
} from '../../common/collapsiblepanel';

import {
  MetadataMergeModel
} from '../model';

import {
  MERGE_CLASSES
} from './common';


const ROOT_METADATA_CLASS = 'jp-Metadata-diff';


/**
 * MetadataWidget for changes to Notebook-level metadata
 */
export
class MetadataMergeWidget extends Panel {
  constructor(model: MetadataMergeModel) {
    super();
    this._model = model;
    this.addClass(ROOT_METADATA_CLASS);
    this.init();
  }

  init() {
    let model = this._model;

    // We know/assume that MetadataMergeModel never has
    // null values for local/remote:
    this.view = createNbdimeMergeView(
      model.remote, model.local, model.merged);
    let wrapper = new CollapsiblePanel(
      this.view, 'Notebook metadata changed', true);
    this.addWidget(wrapper);
  }

  validateMerged(candidate: nbformat.INotebookMetadata): nbformat.INotebookMetadata {
    let text = this.view.getMergedValue();
    if (JSON.stringify(candidate) !== text) {
      // This will need to be validated server side,
      // and should not be touched by client side
      // (structure might differ from assumed form)
      candidate = JSON.parse(text);
    }
    return candidate;
  }

  protected view: MergeView;

  private _model: MetadataMergeModel;
}
