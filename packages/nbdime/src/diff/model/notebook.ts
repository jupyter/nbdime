// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
'use strict';

import {
  nbformat
} from '@jupyterlab/coreutils';

import {
  IDiffEntry, IDiffArrayEntry
} from '../diffentries';

import {
  getSubDiffByKey
} from '../util';

import {
  IStringDiffModel, createPatchStringDiffModel
} from './string';

import {
  CellDiffModel,
  createUnchangedCellDiffModel, createAddedCellDiffModel,
  createDeletedCellDiffModel, createPatchedCellDiffModel
} from './cell';


/**
 * Diff model for a Jupyter Notebook
 */
export class NotebookDiffModel {

  /**
   * Create a new NotebookDiffModel from a base notebook and a list of diffs.
   *
   * The base as well as the diff entries are normally supplied by the nbdime
   * server.
   */
  constructor(base: nbformat.INotebookContent, diff: IDiffEntry[]) {
    // Process global notebook metadata field
    let metaDiff = getSubDiffByKey(diff, 'metadata');
    if (base.metadata && metaDiff) {
      this.metadata = createPatchStringDiffModel(base.metadata, metaDiff);
    } else {
      this.metadata = null;
    }
    if (this.metadata) {
      this.metadata.collapsible = true;
      this.metadata.collapsibleHeader = 'Notebook metadata changed';
      this.metadata.startCollapsed = true;
    }
    // The notebook metadata MIME type is used for determining the MIME type
    // of source cells, so store it easily accessible:
    let mimetype: string | undefined;
    try {
      mimetype = base.metadata.language_info!.mimetype;
    } catch (e) {
      // missing metadata (probably old notebook)
    }
    this.mimetype = mimetype || 'text/python';

    // Build cell diff models. Follows similar logic to patching code:
    this.cells = [];
    this.chunkedCells = [];
    let take = 0;
    let skip = 0;
    let previousChunkIndex = -1;
    let currentChunk: CellDiffModel[] = [];
    for (let e of getSubDiffByKey(diff, 'cells') as IDiffArrayEntry[] || []) {
      let index = e.key;

      // diff is sorted on index, so take any preceding cells as unchanged:
      for (let i=take; i < index; i++) {
        let cell = createUnchangedCellDiffModel(base.cells[i], this.mimetype);
        this.cells.push(cell);
        this.chunkedCells.push([cell]);
      }

      if (index !== previousChunkIndex) {
        currentChunk = [];
        this.chunkedCells.push(currentChunk);
        previousChunkIndex = index;
      }

      // Process according to diff type:
      if (e.op === 'addrange') {
        // One or more inserted/added cells:
        for (let ei of e.valuelist) {
          let cell = createAddedCellDiffModel(ei as nbformat.ICell, this.mimetype);
          this.cells.push(cell);
          currentChunk.push(cell);
        }
        skip = 0;
      } else if (e.op === 'removerange') {
        // One or more removed/deleted cells:
        skip = e.length;
        for (let i=index; i < index + skip; i++) {
          let cell = createDeletedCellDiffModel(base.cells[i], this.mimetype);
          this.cells.push(cell);
          currentChunk.push(cell);
        }
      } else if (e.op === 'patch') {
        // A cell has changed:
        let cell = createPatchedCellDiffModel(base.cells[index], e.diff, this.mimetype);
        this.cells.push(cell);
        currentChunk.push(cell);
        skip = 1;
      }

      // Skip the specified number of elements, but never decrement take.
      // Note that take can pass index in diffs with repeated +/- on the
      // same index, i.e. [op_remove(index), op_add(index, value)]
      take = Math.max(take, index + skip);
    }
    // Take unchanged values at end
    for (let i=take; i < base.cells.length; i++) {
      let cell = createUnchangedCellDiffModel(base.cells[i], this.mimetype);
      this.cells.push(cell);
      this.chunkedCells.push([cell]);
    }
  }

  /**
   * Diff model of the notebook's root metadata field
   */
  metadata: IStringDiffModel | null;

  /**
   * The default MIME type according to the notebook's root metadata
   */
  mimetype: string;

  /**
   * List of all cell diff models, including unchanged, added/removed and
   * changed cells, in order.
   */
  cells: CellDiffModel[];

  /**
   * List of chunks of cells, e.g. so that any changes that occur in the same
   * location optionally can be shown side by side.
   */
  chunkedCells: CellDiffModel[][];
}
