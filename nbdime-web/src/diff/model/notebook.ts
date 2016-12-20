// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
'use strict';

import {
  nbformat
} from '@jupyterlab/services';

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
    let take = 0;
    let skip = 0;
    for (let e of getSubDiffByKey(diff, 'cells') as IDiffArrayEntry[] || []) {
      let index = e.key;

      // diff is sorted on index, so take any preceding cells as unchanged:
      for (let i=take; i < index; i++) {
        this.cells.push(createUnchangedCellDiffModel(
          base.cells[i], this.mimetype));
      }

      // Process according to diff type:
      if (e.op === 'addrange') {
        // One or more inserted/added cells:
        for (let ei of e.valuelist) {
          this.cells.push(createAddedCellDiffModel(
            ei as nbformat.ICell, this.mimetype));
        }
        skip = 0;
      } else if (e.op === 'removerange') {
        // One or more removed/deleted cells:
        skip = e.length;
        for (let i=index; i < index + skip; i++) {
          this.cells.push(createDeletedCellDiffModel(
            base.cells[i], this.mimetype));
        }
      } else if (e.op === 'patch') {
        // A cell has changed:
        this.cells.push(createPatchedCellDiffModel(
          base.cells[index], e.diff, this.mimetype));
        skip = 1;
      }

      // Skip the specified number of elements, but never decrement take.
      // Note that take can pass index in diffs with repeated +/- on the
      // same index, i.e. [op_remove(index), op_add(index, value)]
      take = Math.max(take, index + skip);
    }
    // Take unchanged values at end
    for (let i=take; i < base.cells.length; i++) {
      this.cells.push(createUnchangedCellDiffModel(
        base.cells[i], this.mimetype));
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
}
