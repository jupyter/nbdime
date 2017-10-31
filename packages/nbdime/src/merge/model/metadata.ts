// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
'use strict';

import {
  nbformat
} from '@jupyterlab/coreutils';

import {
  IDiffEntry
} from '../../diff/diffentries';

import {
  IStringDiffModel, createPatchStringDiffModel,
  createDirectStringDiffModel
} from '../../diff/model';

import {
  MergeDecision
} from '../../merge/decisions';

import {
    ObjectMergeModel, DecisionStringDiffModel
} from './common';


/**
 * Model of a merge of metadata with decisions
 */
export
class MetadataMergeModel extends ObjectMergeModel<nbformat.INotebookMetadata, IStringDiffModel> {
  constructor(base: nbformat.INotebookMetadata, decisions: MergeDecision[]) {
    super(base, decisions, 'application/json');
  }

  serialize(): nbformat.INotebookMetadata {
    if (!this.merged || this.merged.remote === null) {
      throw new Error('Missing notebook metadata merge data.');
    }
    // This will check whether metadata is valid JSON.
    // Validation of compatibility vs notebook format
    // will happen on server side.
    return JSON.parse(this.merged.remote);
  }

  protected createDiffModel(diff: IDiffEntry[]): IStringDiffModel {
    if (diff && diff.length > 0) {
      return createPatchStringDiffModel(this.base, diff);
    } else {
      return createDirectStringDiffModel(this.base, this.base);
    }
  }

  protected createMergedDiffModel(): IStringDiffModel {
    return new DecisionStringDiffModel(
      this.base, this.decisions,
      [this.local, this.remote]);
  }

  base: nbformat.INotebookMetadata;
}
