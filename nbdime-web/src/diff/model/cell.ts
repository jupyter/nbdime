// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
'use strict';

import {
  nbformat
} from 'jupyterlab/lib/notebook/notebook/nbformat';

import {
  NotifyUserError
} from '../../common/exceptions';

import {
  IDiffEntry, IDiffArrayEntry
} from '../diffentries';

import {
  getSubDiffByKey
} from '../util';

import {
  IStringDiffModel, StringDiffModel, createDirectStringDiffModel,
  createPatchStringDiffModel, setMimetypeFromCellType
} from './string';

import {
  OutputDiffModel, makeOutputModels
} from './output';



/**
 * Diff model for individual Notebook Cells
 */
export class CellDiffModel {
  constructor(source: IStringDiffModel, metadata: IStringDiffModel,
              outputs: OutputDiffModel[] | null, cellType: string) {
    this.source = source;
    this.metadata = metadata;
    this.outputs = outputs;
    this.cellType = cellType;
    if (outputs === null && cellType === 'code') {
      throw new NotifyUserError('Invalid code cell, missing outputs!');
    }
    this.metadata.collapsible = true;
    this.metadata.collapsibleHeader = 'Metadata changed';
    this.metadata.startCollapsed = true;
  }

  /**
   * Diff model for the source field.
   */
  source: IStringDiffModel;

  /**
   * Diff model for the metadata field.
   */
  metadata: IStringDiffModel;

  /**
   * Diff model for the outputs field. Can be null.
   *
   * A null value signifies that the cell is not a
   * code cell type.
   */
  outputs: OutputDiffModel[] | null;

  /**
   * The type of the notebook cell
   */
  cellType: string;


  /**
   * Whether the cell has remained unchanged
   */
  get unchanged(): boolean {
    let unchanged = this.source.unchanged;
    unchanged = unchanged &&
      (this.metadata ? this.metadata.unchanged : true);
    if (this.outputs) {
      for (let o of this.outputs) {
        unchanged = unchanged && o.unchanged;
      }
    }
    return unchanged;
  }

  /**
   * Whether the cell has been added to the notebook (new cell)
   */
  get added(): boolean {
    return this.source.added;
  }

  /**
   * Whether the cell has been deleted/removed from the notebook
   */
  get deleted(): boolean {
    return this.source.deleted;
  }
}

export
function createPatchedCellDiffModel(
    base: nbformat.ICell, diff: IDiffEntry[] | null, nbMimetype: string): CellDiffModel {
  let source: StringDiffModel | null = null;
  let metadata: StringDiffModel | null = null;
  let outputs: OutputDiffModel[] | null = null;

  let subDiff = getSubDiffByKey(diff, 'source');
  if (subDiff) {
    source = createPatchStringDiffModel(base.source, subDiff);
  } else {
    source = createDirectStringDiffModel(base.source, base.source);
  }
  setMimetypeFromCellType(source, base, nbMimetype);

  subDiff = getSubDiffByKey(diff, 'metadata');
  metadata = subDiff ?
    createPatchStringDiffModel(base.metadata, subDiff) :
    createDirectStringDiffModel(base.metadata, base.metadata);

  if (base.cell_type === 'code') {
    let outputsBase = (base as nbformat.ICodeCell).outputs;
    let outputsDiff = getSubDiffByKey(diff, 'outputs') as IDiffArrayEntry[];
    if (outputsDiff) {
      // Outputs patched
      outputs = makeOutputModels(
        outputsBase, null, outputsDiff);
    } else {
      // Outputs unchanged
      outputs = makeOutputModels(
        outputsBase, outputsBase);
    }
  }
  return new CellDiffModel(source, metadata, outputs, base.cell_type);
}

export
function createUnchangedCellDiffModel(
      base: nbformat.ICell, nbMimetype: string): CellDiffModel {
  let source = createDirectStringDiffModel(base.source, base.source);
  setMimetypeFromCellType(source, base, nbMimetype);
  let metadata = createDirectStringDiffModel(base.metadata, base.metadata);
  let outputs: OutputDiffModel[] | null = null;
  if (base.cell_type === 'code') {
    outputs = makeOutputModels((base as nbformat.ICodeCell).outputs,
      (base as nbformat.ICodeCell).outputs);
  }
  return new CellDiffModel(source, metadata, outputs, base.cell_type);
}

export
function createAddedCellDiffModel(
      remote: nbformat.ICell, nbMimetype: string): CellDiffModel {
  let source = createDirectStringDiffModel(null, remote.source);
  setMimetypeFromCellType(source, remote, nbMimetype);
  let metadata = createDirectStringDiffModel(null, remote.metadata);
  let outputs: OutputDiffModel[] | null = null;
  if (remote.cell_type === 'code') {
    outputs = makeOutputModels(
      null, (remote as nbformat.ICodeCell).outputs);
  }
  return new CellDiffModel(source, metadata, outputs, remote.cell_type);
}

export
function createDeletedCellDiffModel(
      base: nbformat.ICell, nbMimetype: string): CellDiffModel {
  let source = createDirectStringDiffModel(base.source, null);
  setMimetypeFromCellType(source, base, nbMimetype);
  let metadata = createDirectStringDiffModel(base.metadata, null);
  let outputs: OutputDiffModel[] | null = null;
  if (base.cell_type === 'code') {
    outputs = makeOutputModels((base as nbformat.ICodeCell).outputs, null);
  }
  return new CellDiffModel(source, metadata, outputs, base.cell_type);
}