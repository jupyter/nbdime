// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
'use strict';

import {
  IRenderMime
} from 'jupyterlab/lib/rendermime';

import {
  Panel, PanelLayout
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
class NotebookDiffWidget extends Panel {
  constructor(model: NotebookDiffModel, rendermime: IRenderMime) {
    super();
    this._model = model;
    this._rendermime = rendermime;
    this.addClass(NBDIFF_CLASS);
  }

  /**
   * Start adding sub-widgets.
   *
   * Separated from constructor to allow 'live' adding of widgets
   */
  init(): Promise<void> {
    let model = this._model;
    let rendermime = this._rendermime;

    let work = Promise.resolve();
    work = work.then(() => {
      if (model.metadata) {
        this.addWidget(new MetadataDiffWidget(model.metadata));
      }
    });
    for (let c of model.cells) {
      work = work.then(() => {
        return new Promise<void>(resolve => {
          this.addWidget(new CellDiffWidget(c, rendermime, model.mimetype));
          // This limits us to drawing 60 cells per second, which shoudln't
          // be a problem...
          requestAnimationFrame(() => {
            resolve();
          });
        });
      });
    }
    return work;
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
