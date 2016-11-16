// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
'use strict';

import {
  IRenderMime
} from 'jupyterlab/lib/rendermime';

import {
  Widget
} from 'phosphor/lib/ui/widget';

import {
  PanelLayout
} from 'phosphor/lib/ui/panel';

import {
  CellDiffWidget
} from './cell';

import {
  MetadataDiffWidget
} from './metadata';

import {
  NotebookDiffModel
} from '../model';


const NBDIFF_CLASS = 'jp-Notebook-diff';


/**
 * NotebookDiffWidget
 */
export
class NotebookDiffWidget extends Widget {
  constructor(model: NotebookDiffModel, rendermime: IRenderMime) {
    super();
    this._model = model;
    this._rendermime = rendermime;
    let layout = this.layout = new PanelLayout();

    this.addClass(NBDIFF_CLASS);

    if (model.metadata) {
      layout.addWidget(new MetadataDiffWidget(model.metadata));
    }
    for (let c of model.cells) {
      layout.addWidget(new CellDiffWidget(c, rendermime, model.mimetype));
    }
  }

  /**
   * Get the model for the widget.
   *
   * #### Notes
   * This is a read-only property.
   */
  get model(): NotebookDiffModel {
    return this._model;
  }

  private _model: NotebookDiffModel;
  private _rendermime: IRenderMime;
}
