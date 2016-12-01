// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
'use strict';

import {
  Widget
} from 'phosphor/lib/ui/widget';

import {
  Panel
} from 'phosphor/lib/ui/panel';

import {
  createNbdimeMergeView
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
    let view: Widget = createNbdimeMergeView(
      model.remote, model.local, model.merged);
    view = new CollapsiblePanel(
      view, 'Notebook metadata changed', true);
    this.addWidget(view);
  }

  private _model: MetadataMergeModel;
}
