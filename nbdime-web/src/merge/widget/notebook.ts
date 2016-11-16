// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
'use strict';

import {
  IRenderMime
} from 'jupyterlab/lib/rendermime';

import {
  DragDropPanel
} from '../../common/dragpanel';

import {
  PanelLayout
} from 'phosphor/lib/ui/panel';

import {
  NotebookMergeModel
} from '../model';

import {
  MetadataMergeWidget
} from './metadata';

import {
  CellMergeWidget
} from './cell';


const NBMERGE_CLASS = 'jp-Notebook-merge';


/**
 * NotebookMergeWidget
 */
export
class NotebookMergeWidget extends DragDropPanel {
  constructor(model: NotebookMergeModel,
              rendermime: IRenderMime) {
    super();
    this._model = model;
    this._rendermime = rendermime;
    let layout = this.layout as PanelLayout;

    this.addClass(NBMERGE_CLASS);

    if (model.metadata.decisions.length > 0) {
      layout.addWidget(new MetadataMergeWidget(model.metadata));
    }
    for (let c of model.cells) {
      layout.addWidget(new CellMergeWidget(c, rendermime, model.mimetype));
    }
  }

  /**
   * Get the model for the widget.
   *
   * #### Notes
   * This is a read-only property.
   */
  get model(): NotebookMergeModel {
    return this._model;
  }

  protected move(from: number, to: number): void {
    // Move cell in model list
    this._model.cells.splice(to, 0, this._model.cells.splice(from, 1)[0]);
    super.move(from, to);
  }

  private _model: NotebookMergeModel;
  private _rendermime: IRenderMime;
}
