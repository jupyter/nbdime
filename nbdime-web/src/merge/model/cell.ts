// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
'use strict';

import {
  nbformat
} from 'jupyterlab/lib/notebook/notebook/nbformat';

import {
  defineSignal, ISignal
} from 'phosphor/lib/core/signaling';

import {
  IDiffAddRange, IDiffPatch, IDiffEntry, IDiffArrayEntry
} from '../../diff/diffentries';

import {
  CellDiffModel,
  createAddedCellDiffModel, createDeletedCellDiffModel,
  createPatchedCellDiffModel, createUnchangedCellDiffModel,
  OutputDiffModel, makeOutputModels,
  setMimetypeFromCellType
} from '../../diff/model';

import {
  MergeDecision, resolveCommonPaths, buildDiffs,
  filterDecisions, pushPatchDecision, popPath, applyDecisions
} from '../../merge/decisions';

import {
  patch
} from '../../patch';

import {
  arraysEqual, valueIn, hasEntries
} from '../../common/util';

import {
  ObjectMergeModel, DecisionStringDiffModel
} from './common';


/**
 * Create a cell diff model based on a set of merge
 * decisions that patch the cell.
 */
function createPatchedCellDecisionDiffModel(
    base: nbformat.ICell, decisions: MergeDecision[],
    local: CellDiffModel | null, remote: CellDiffModel | null,
    mimetype: string):
    CellDiffModel {

  for (let md of decisions) {
    if (md.localPath.length === 0) {
      let val = popPath(md.diffs, true);
      if (val === null) {
        throw new Error('Invalid diffs for patching cell!');
      }
      md.diffs = val.diffs;
      md.pushPath(val.key);
    }
  }

  let source = new DecisionStringDiffModel(
    base.source, filterDecisions(decisions, ['source'], 2),
    [local ? local.source : null,
     remote ? remote.source : null]);
  setMimetypeFromCellType(source, base, mimetype);

  let metadata = new DecisionStringDiffModel(
    base.metadata, filterDecisions(decisions, ['metadata'], 2),
    [local ? local.metadata : null,
      remote ? remote.metadata : null]);

  let outputs: OutputDiffModel[] | null = null;
  if (base.cell_type === 'code' && (base as nbformat.ICodeCell).outputs) {
    let outputBase = (base as nbformat.ICodeCell).outputs;
    let outputDec = filterDecisions(decisions, ['outputs'], 2);
    let mergedDiff = buildDiffs(outputBase, outputDec, 'merged') as IDiffArrayEntry[];
    let merged: nbformat.IOutput[];
    if (mergedDiff && mergedDiff.length > 0) {
      merged = patch(outputBase, mergedDiff);
    } else {
      merged = outputBase;
    }
    outputs = makeOutputModels(outputBase, merged, mergedDiff);
  }
  return new CellDiffModel(source, metadata, outputs, base.cell_type);
}


/**
 * CellMergeModel
 */
export
class CellMergeModel extends ObjectMergeModel<nbformat.ICell, CellDiffModel> {
  constructor(base: nbformat.ICell | null, decisions: MergeDecision[], mimetype: string) {
    // TODO: Remove/extend whitelist once we support more
    super(base, [], mimetype, ['source', 'metadata', 'outputs']);
    this.onesided = false;
    this._deleteCell = false;
    this.processDecisions(decisions);
  }

  /**
   * Whether the cell is present in only one of the two side (local/remote)
   */
  onesided: boolean;

  /**
   * Run time flag whether the user wants to delete the cell or not
   */
  get deleteCell(): boolean {
    return this._deleteCell;
  }
  set deleteCell(value: boolean) {
    if (this._deleteCell !== value) {
      this._deleteCell = value;
      this.deleteCellChanged.emit(value);
    }
  }
  _deleteCell: boolean;

  deleteCellChanged: ISignal<CellMergeModel, boolean>;

  /**
   * Whether source is the same in local and remote
   */
  get agreedSource(): boolean {
    return !!this.local && !!this.remote &&
      this.local.source.remote === this.remote.source.remote;
  }

  /**
   * Whether metadata is the same in local and remote
   */
  get agreedMetadata(): boolean {
    if (!this.local || !this.remote) {
      return false;
    }
    return this.local.metadata.remote === this.remote.metadata.remote;
  }

  /**
   * Whether outputs are the same in local and remote
   */
  get agreedOutputs(): boolean {
    if (!this.local || !this.remote) {
      return false;
    }
    let lo = this.local.outputs;
    let ro = this.remote.outputs;
    if (!hasEntries(lo) || !hasEntries(ro)) {
      return !hasEntries(lo) && !hasEntries(ro);
    }
    if (lo.length !== ro.length) {
      return false;
    }
    for (let i=0; i < lo.length; ++i) {
      if (JSON.stringify(lo[i].remote) !== JSON.stringify(ro[i].remote)) {
        return false;
      }
    }
    return true;
  }

  /**
   * Whether cell is the same in local and remote
   */
  get agreedCell(): boolean {
    // TODO: Also check other fields?
    return this.agreedSource && this.agreedMetadata && this.agreedOutputs;
  }

  /**
   * Apply merge decisions to create the merged cell
   */
  serialize(): nbformat.ICell | null {
    if (this.base === null) {
      return null;
    }
    let decisions: MergeDecision[] = [];
    for (let md of this.decisions) {
      let nmd = new MergeDecision(md);
      nmd.level = 2;
      decisions.push(nmd);
    }
    return applyDecisions(this.base, decisions);
  }

  protected processDecisions(decisions: MergeDecision[]): void {
    // First check for cell-level decisions:
    if (decisions.length === 1) {
      if (arraysEqual(decisions[0].absolutePath, ['cells'])) {
        // We have a cell level decision
        let md = decisions[0];
        decisions = this.applyCellLevelDecision(md);
      }
    }

    for (let md of decisions) {
      md.level = 2;
      if (md.absolutePath.length < 2 ||
          md.absolutePath[0] !== 'cells') {
        throw new Error('Not a valid path for a cell decision');
      } else if (md.absolutePath.length === 2 && (
            hasEntries(md.localDiff) || hasEntries(md.remoteDiff))) {
        // Have decision on /cells/X/. Such decisions should always
        // be onsided.
        if (hasEntries(md.localDiff) && hasEntries(md.remoteDiff)) {
          // Not onesided.
          throw new Error('Invalid merge decision: ' + md);
        }
        // Split the decision on subkey:

        // Nest diff as a patch on cell, which can be split by `splitPatch`:
        let splitDec = pushPatchDecision(md, md.absolutePath.slice(1, 2));
        let diff = (hasEntries(splitDec.localDiff) ?
          splitDec.localDiff : splitDec.remoteDiff!);
        let subDecisions = this.splitPatch(
          splitDec, diff[0] as IDiffPatch,
          hasEntries(splitDec.localDiff));
        resolveCommonPaths(subDecisions);
        // Add all split decisions
        for (let subdec of subDecisions) {
          subdec.level = 2;
          this.decisions.push(subdec);
        }
      } else { // Decision has path on subkey
        // Make local path relative to cell
        this.decisions.push(md);
      }
    }


  }

  /**
   * Apply a cell level decision to the model
   *
   * This creates the revelant kinds of models
   */
  protected applyCellLevelDecision(md: MergeDecision): MergeDecision[] {
    let newDecisions: MergeDecision[] = [];
    /* Possibilities:
     1. Insertion: base is null! Null diff of missing side (unchanged).
     2. Deletion: Null diff of present side (unchanged). Set deleteCell
        depending on action.
     3. Deletion vs patch: Same as 2., but split patch decision onto
        source/metadata/outputs.
     4. Identical ops (insertion or deletion)
     Cases that shouldn't happen:
     5. Insertion vs insertion: Shouldn't happen! Should have been split
        into two decisions with an insertion each before creating model.
     6. Patch vs patch: Shouldn't occur, as those should have been recursed
     */
    console.assert(!this.onesided,
                   'Cannot have multiple cell decisions on one cell!');
    this.onesided = true;  // We set this to distinguish case 3 from normal
    if (!hasEntries(md.localDiff)) {
      // 1. or 2.:
      this._local = null;
      if (!md.remoteDiff || md.remoteDiff.length !== 1) {
        throw new Error('Merge decision does not conform to expectation: ' + md);
      }
      if (this.base === null) {
        // 1.
        let first = md.remoteDiff[0];
        if (first.op !== 'addrange') {
          throw new Error('Merge decision does not conform to expectation: ' + md);
        }
        let v = first.valuelist[0] as nbformat.ICell;
        this._remote = createAddedCellDiffModel(v, this.mimetype);
        this._merged = createAddedCellDiffModel(v, this.mimetype);
      } else {
        // 2.
        this._remote = createDeletedCellDiffModel(this.base, this.mimetype);
        this._merged = createDeletedCellDiffModel(this.base, this.mimetype);
        this.deleteCell = valueIn(md.action, ['remote', 'either']);
      }
    } else if (!hasEntries(md.remoteDiff)) {
      // 1. or 2.:
      this._remote = null;
      if (!md.localDiff || md.localDiff.length !== 1) {
        throw new Error('Merge decision does not conform to expectation: ' + md);
      }
      if (this.base === null) {
        // 1.
        let first = md.localDiff[0];
        if (first.op !== 'addrange') {
          throw new Error('Merge decision does not conform to expectation: ' + md);
        }
        let v = first.valuelist[0] as nbformat.ICell;
        this._local = createAddedCellDiffModel(v, this.mimetype);
        this._merged = createAddedCellDiffModel(v, this.mimetype);
      } else {
        // 2.
        this._local = createDeletedCellDiffModel(this.base, this.mimetype);
        this._merged = createDeletedCellDiffModel(this.base, this.mimetype);
        this.deleteCell = valueIn(md.action, ['local', 'either']);
      }
    } else {
      console.assert(hasEntries(md.localDiff) && hasEntries(md.remoteDiff));
      console.assert(md.localDiff.length === 1 && md.remoteDiff.length === 1);
      // 3. or 4.
      if (md.localDiff[0].op === md.remoteDiff[0].op) {
        // 4.
        if (this.base === null) {
          // Identical insertions (this relies on preprocessing to ensure only
          // one value in valuelist)
          let v = (md.localDiff[0] as IDiffAddRange).valuelist[0];
          this._local = createAddedCellDiffModel(v, this.mimetype);
          this._remote = createAddedCellDiffModel(v, this.mimetype);
          this._merged = createAddedCellDiffModel(v, this.mimetype);
        } else {
          // Identical delections
          this._local = createDeletedCellDiffModel(this.base, this.mimetype);
          this._remote = createDeletedCellDiffModel(this.base, this.mimetype);
          this._merged = createDeletedCellDiffModel(this.base, this.mimetype);
          this.deleteCell = valueIn(md.action, ['local', 'remote', 'either']);
        }
      } else {
        // 3., by method of elimination
        let ops = [md.localDiff[0].op, md.remoteDiff[0].op];
        console.assert(
          valueIn('removerange', ops) && valueIn('patch', ops));
        if (this.base === null) {
          throw new Error('Invalid merge decision, ' +
            'cannot have null base for deleted cell: ' + md);
        }
        if (ops[0] === 'removerange') {
          this._local = createDeletedCellDiffModel(this.base, this.mimetype);
          this.deleteCell = md.action === 'local';
          // The patch op will be on cell level. Split it on sub keys!
          newDecisions = newDecisions.concat(this.splitPatch(
            md, md.remoteDiff[0] as IDiffPatch, false));
        } else {
          this._remote = createDeletedCellDiffModel(this.base, this.mimetype);
          this.deleteCell = md.action === 'remote';
          // The patch op will be on cell level. Split it on sub keys!
          newDecisions = newDecisions.concat(this.splitPatch(
            md, md.localDiff[0] as IDiffPatch, true));
        }
        resolveCommonPaths(newDecisions);
      }
    }
    return newDecisions;
  }

  protected createDiffModel(diff: IDiffEntry[]): CellDiffModel {
    if (this.base === null) {
      throw new Error('Cannot create a patched or unchanged diff model with null base!');
    }
    if (diff && diff.length > 0) {
      return createPatchedCellDiffModel(this.base, diff, this.mimetype);
    } else {
      return createUnchangedCellDiffModel(this.base, this.mimetype);
    }
  }

  protected createMergedDiffModel(): CellDiffModel {
    if (this.base === null) {
      throw new Error('Cannot create a patched or unchanged merged diff model with null base!');
    }
    return createPatchedCellDecisionDiffModel(
        this.base, this.decisions, this.local, this.remote, this.mimetype);
  }
}

defineSignal(CellMergeModel.prototype, 'deleteCellChanged');
