// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
"use strict";

import { Panel } from "@lumino/widgets";

import type {
  IRenderMimeRegistry
} from '@jupyterlab/rendermime';

import { LazyDisplayLinkedListCell, LinkedListCell } from "./linked-cells";
import { CellDiffWidget } from "./cell";
import {
  CHUNK_PANEL_CLASS,
  ADDED_CHUNK_PANEL_CLASS,
  REMOVED_CHUNK_PANEL_CLASS,
} from "./common";

import { MetadataDiffWidget } from "./metadata";

import { NotebookDiffModel, CellDiffModel } from "../model";

const NBDIFF_CLASS = "jp-Notebook-diff";

/**
 * NotebookDiffWidget
 */
export class NotebookDiffWidget extends Panel {
  constructor(model: NotebookDiffModel, rendermime: IRenderMimeRegistry) {
    super();
    this._model = model;
    this._rendermime = rendermime;
    this.addClass(NBDIFF_CLASS);
    this.previousCell = null;
  }

  /**
   * Start adding sub-widgets.
   *
   * Separated from constructor to allow 'live' adding of widgets
   */
  init(): Promise<void> {
    const model = this._model;

    let work = Promise.resolve();
    // eslint-disable-next-line github/no-then
    work = work.then(() => {
      if (model.metadata) {
        this.addWidget(new MetadataDiffWidget(model.metadata));
      }
    });
    for (const chunk of model.chunkedCells) {
      // eslint-disable-next-line github/no-then
      work = work.then(() => {
        return new Promise<void>((resolve) => {
          this.addDiffChunk(chunk);
          // This limits us to drawing 60 cells per second, which shouldn't
          // be a problem...
          requestAnimationFrame(() => {
            resolve();
          });
        });
      });
    }
    return work;
  }

  private addDiffChunk(chunk: CellDiffModel[]): void {
    console.log("Adding chunk");
    console.log(this.previousCell);
    if (chunk.length === 1 && !(chunk[0].added || chunk[0].deleted)) {
      this.addWidget(this.addCellPanel(chunk[0]));
    } else {
      this.addChunkPanel(chunk);
    }
  }

  private addChunkPanel(chunk: CellDiffModel[]): void {
    const chunkPanel = new Panel();
    chunkPanel.addClass(CHUNK_PANEL_CLASS);
    const addedPanel = new Panel();
    addedPanel.addClass(ADDED_CHUNK_PANEL_CLASS);
    const removedPanel = new Panel();
    removedPanel.addClass(REMOVED_CHUNK_PANEL_CLASS);
    for (const cell of chunk) {
      const target = cell.deleted ? removedPanel : addedPanel;
      target.addWidget(this.addCellPanel(cell));
    }

    chunkPanel.addWidget(addedPanel);
    chunkPanel.addWidget(removedPanel);
    this.addWidget(chunkPanel);
  }

  private addCellPanel(
    cell: CellDiffModel
  ): LinkedListCell | LazyDisplayLinkedListCell {
    let linkedCell: LinkedListCell | LazyDisplayLinkedListCell;
    if (cell.unchanged) {
      linkedCell = new LazyDisplayLinkedListCell(() =>
        this.creatCellWidget(cell)
      );
    } else {
      linkedCell = new LinkedListCell(() => this.creatCellWidget(cell));
    }
    if (this.previousCell) {
      linkedCell.prev = this.previousCell;
    }
    this.previousCell = linkedCell;
    return linkedCell;
  }

  creatCellWidget(cell: CellDiffModel): CellDiffWidget {
    const cellWidget = new CellDiffWidget(
      cell,
      this._rendermime,
      this._model.mimetype
    );
    const outputMenu = cellWidget.node.querySelector(".jp-Diff-outputMenu");

    if (outputMenu) {
      // We never want to trust any cells, so remove the interface from the UI.
      const trustButton = outputMenu.querySelector(
        ".jp-Diff-trustOutputButton"
      );
      trustButton && outputMenu.removeChild(trustButton);
    }
    return cellWidget;
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
  private _rendermime: IRenderMimeRegistry;
  private previousCell: LinkedListCell | null;
}
