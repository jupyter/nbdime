// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
'use strict';

import {
  Panel, Widget
} from '@phosphor/widgets';

import {
  createNbdimeMergeView
} from '../../common/mergeview';

import {
  CollapsiblePanel
} from '../../common/collapsiblepanel';

import {
  IStringDiffModel
} from '../model';

import {
  DIFF_CLASSES, TWOWAY_DIFF_CLASS
} from './common';


const ROOT_METADATA_CLASS = 'jp-Metadata-diff';


/**
 * MetadataWidget for changes to Notebook-level metadata
 */
export
class MetadataDiffWidget extends Panel {
  constructor(model: IStringDiffModel) {
    super();
    this._model = model;
    console.assert(!model.added && !model.deleted);
    this.addClass(ROOT_METADATA_CLASS);
    this.init();
  }

  init() {
    let model = this._model;
    if (!model.unchanged) {
      this.addClass(TWOWAY_DIFF_CLASS);
      let view: Widget = createNbdimeMergeView(model);
      if (model.collapsible) {
        view = new CollapsiblePanel(
          view, model.collapsibleHeader, model.startCollapsed);
      }
      this.addWidget(view);
    }
  }

  private _model: IStringDiffModel;
}
