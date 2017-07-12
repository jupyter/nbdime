// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
'use strict';

import {
  nbformat
} from '@jupyterlab/coreutils';

import {
  Signal
} from '@phosphor/signaling';

import {
  IDiffAddRange, IDiffEntry, IDiffArrayEntry,
  IDiffPatchObject, IDiffImmutableObjectEntry
} from '../../diff/diffentries';

import {
  getDiffEntryByKey
} from '../../diff/util';

import {
  CellDiffModel,
  createAddedCellDiffModel, createDeletedCellDiffModel,
  createPatchedCellDiffModel, createUnchangedCellDiffModel,
  OutputDiffModel, makeOutputModels, ImmutableDiffModel,
  setMimetypeFromCellType, createImmutableModel
} from '../../diff/model';

import {
  MergeDecision, resolveCommonPaths, buildDiffs, decisionSortKey,
  filterDecisions, pushPatchDecision, popPath, applyDecisions,
  Action
} from '../../merge/decisions';

import {
  patch
} from '../../patch';

import {
  arraysEqual, valueIn, hasEntries, splitLines, unique, stableSort
} from '../../common/util';

import {
  splitMergeDecisionsOnChunks
} from '../../chunking';

import {
  ObjectMergeModel, DecisionStringDiffModel
} from './common';


import {
  NotifyUserError
} from '../../common/exceptions';


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
      if (val !== null) {
        md.diffs = val.diffs;
        md.pushPath(val.key);
      }
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
  let executionCount: ImmutableDiffModel | null = null;
  if (nbformat.isCode(base)) {
    if (base.outputs) {
      let outputBase = base.outputs;
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
    let execBase = base.execution_count;
    let cellDecs = filterDecisions(decisions, ['cells'], 0, 2);
    for (let dec of cellDecs) {
      if (getDiffEntryByKey(dec.localDiff, 'execution_count') !== null ||
          getDiffEntryByKey(dec.remoteDiff, 'execution_count') !== null ||
          getDiffEntryByKey(dec.customDiff, 'execution_count') !== null) {
        dec.level = 2;
        let mergeExecDiff = buildDiffs(base, [dec], 'merged') as IDiffImmutableObjectEntry[] | null;
        let execDiff = hasEntries(mergeExecDiff) ? mergeExecDiff[0] : null;
        // Pass base as remote, which means fall back to unchanged if no diff:
        executionCount = createImmutableModel(execBase, execBase, execDiff);
      }
    }

  }

  return new CellDiffModel(source, metadata, outputs, executionCount, base.cell_type);
}


/**
 * CellMergeModel
 */
export
class CellMergeModel extends ObjectMergeModel<nbformat.ICell, CellDiffModel> {
  constructor(base: nbformat.ICell | null, decisions: MergeDecision[], mimetype: string) {
    // TODO: Remove/extend whitelist once we support more
    super(base, [], mimetype, ['source', 'metadata', 'outputs', 'execution_count']);
    this.onesided = false;
    this._deleteCell = false;
    this.processDecisions(decisions);
  }

  /**
   * Whether the cell is present in only one of the two side (local/remote)
   */
  onesided: boolean;

  /**
   * Run time flag whether the user wants to delete the cell
   *
   * @type {boolean}
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
  private _deleteCell: boolean;

  readonly deleteCellChanged = new Signal<CellMergeModel, boolean>(this);


  /**
   * Run time flag whether the user wants to clear the outputs of the cell
   *
   * @type {boolean}
   */
  get clearOutputs(): boolean {
    return this._clearOutputs;
  }
  set clearOutputs(value: boolean) {
    if (this._clearOutputs !== value) {
      this._clearOutputs = value;
      this.clearOutputsChanged.emit(value);
    }
  }
  private _clearOutputs = false;

  readonly clearOutputsChanged = new Signal<CellMergeModel, boolean>(this);

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
   * Whether the cell has any conflicted decisions.
   */
  get conflicted(): boolean {
    for (let dec of this.decisions) {
      if (dec.conflict) {
        return true;
      }
    }
    return false;
  }

  /**
   * Whether the cell has any conflicted decisions on a specific key.
   */
  hasConflictsOn(key: string) {
    let decs = filterDecisions(this.decisions, [key], 2);
    for (let dec of decs) {
      if (dec.conflict) {
        return true;
      }
    }
    return false;
  }

  /**
   * Whether the cell has any conflicted decisions on source.
   */
  get sourceConflicted(): boolean {
    return this.hasConflictsOn('source');
  }

  /**
   * Whether the cell has any conflicted decisions on metadata.
   */
  get metadataConflicted(): boolean {
    return this.hasConflictsOn('metadata');
  }

  /**
   * Whether the cell has any conflicted decisions.
   */
  get outputsConflicted(): boolean {
    return this.hasConflictsOn('outputs');
  }

  /**
   * Clear any conflicts on decisions on outputs
   */
  clearOutputConflicts() {
    let decs = filterDecisions(this.decisions, ['outputs'], 2);
    for (let dec of decs) {
      dec.conflict = false;
    }
  }

  /**
   * Get the decision on `execution_count` field (should only be one).
   *
   * Returns null if no decision on `execution_count` was found.
   */
  getExecutionCountDecision(): MergeDecision | null {
    let cellDecs = filterDecisions(this.decisions, ['cells'], 0, 2);
    for (let dec of cellDecs) {
      if (getDiffEntryByKey(dec.localDiff, 'execution_count') !== null ||
          getDiffEntryByKey(dec.remoteDiff, 'execution_count') !== null ||
          getDiffEntryByKey(dec.customDiff, 'execution_count') !== null) {
        return dec;
      }
    }
    return null;
  }

  /**
   * Apply merge decisions to create the merged cell
   */
  serialize(): nbformat.ICell | null {
    if (this.deleteCell) {
      return null;
    }
    if (this.base === null) {
      // Only possibility is that cell is added
      if (this.decisions.length > 1 || !this.merged.added) {
        throw new NotifyUserError('Invalid cell decision');
      }
      let dec = this.decisions[0];
      // Either onesided or identical inserts, but possibly with
      // a custom diff on top!
      let d: IDiffEntry;
      if (dec.action === 'local' || dec.action === 'either') {
        if (!dec.localDiff ) {
          throw new NotifyUserError('Invalid cell decision');
        }
        d = dec.localDiff[0];
      } else if (dec.action === 'remote') {
        if (!dec.remoteDiff ) {
          throw new NotifyUserError('Invalid cell decision');
        }
        d = dec.remoteDiff[0];
      } else if (dec.action === 'custom') {
        if (!dec.customDiff ) {
          throw new NotifyUserError('Invalid cell decision');
        }
        d = dec.customDiff[0];
      } else {
        throw new NotifyUserError('Invalid cell decision');
      }
      if (d.op !== 'addrange') {
        throw new NotifyUserError('Invalid cell decision');
      }
      return d.valuelist[0];
    }
    let decisions: MergeDecision[] = [];
    for (let md of this.decisions) {
      let nmd = new MergeDecision(md);
      nmd.level = 2;
      decisions.push(nmd);
    }
    let output = applyDecisions(this.base, decisions);
    let src = output.source;
    if (Array.isArray(src)) {
      src = src.join('');
    }
    if (src !== this._merged!.source.remote) {
      console.warn('Serialized outputs doesn\'t match model value! ' +
                   'Keeping the model value.');
      output.source = splitLines(this._merged!.source.remote!);
    }
    if (this.clearOutputs && nbformat.isCode(output)) {
      output.outputs = [];
    }
    return output;
  }

  protected processDecisions(decisions: MergeDecision[]): void {
    // First check for cell-level decisions:
    if (decisions.length === 1) {
      if (arraysEqual(decisions[0].absolutePath, ['cells'])) {
        // We have a cell level decision
        let md = decisions[0];
        decisions = this.applyCellLevelDecision(md);
        if (decisions.length === 0) {
          this.decisions.push(md);
        }
      }
    }

    for (let md of decisions) {
      md.level = 2;
      if (md.absolutePath.length < 2 ||
          md.absolutePath[0] !== 'cells') {
        throw new Error('Not a valid path for a cell decision');
      } else if (md.absolutePath.length === 2 && (
            hasEntries(md.localDiff) || hasEntries(md.remoteDiff))) {
        // Have decision on /cells/X/.
        // Split the decision on subkey:

        // Nest diff as a patch on cell, which can be split by `splitPatch`:
        let splitDec = pushPatchDecision(md, md.absolutePath.slice(1, 2));
        let localDiff = hasEntries(splitDec.localDiff) ?
          splitDec.localDiff[0] as IDiffPatchObject : null;
        let remoteDiff = hasEntries(splitDec.remoteDiff) ?
          splitDec.remoteDiff[0] as IDiffPatchObject : null;

        let subDecisions = this.splitPatch(splitDec, localDiff, remoteDiff);
        // Add all split decisions:
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
            md, null, md.remoteDiff[0] as IDiffPatchObject));
        } else {
          this._remote = createDeletedCellDiffModel(this.base, this.mimetype);
          this.deleteCell = md.action === 'remote';
          // The patch op will be on cell level. Split it on sub keys!
          newDecisions = newDecisions.concat(this.splitPatch(
            md, md.localDiff[0] as IDiffPatchObject, null));
        }
        resolveCommonPaths(newDecisions);
      }
    }
    return newDecisions;
  }


   /**
    * Split a decision with a patch on one side into one decision
    * for each sub entry in the patch.
    */
  protected splitPatch(md: MergeDecision, localPatch: IDiffPatchObject | null, remotePatch: IDiffPatchObject | null): MergeDecision[] {
    let local = !!localPatch && hasEntries(localPatch.diff);
    let remote = !!remotePatch && hasEntries(remotePatch.diff);
    if (!local && !remote) {
      return [];
    }
    let localDiff = local ? localPatch!.diff : null;
    let remoteDiff = remote ? remotePatch!.diff : null;
    let split: MergeDecision[] = [];
    let keys: (string | number)[] = [];
    if (local) {
      for (let d of localDiff!) {
        keys.push(d.key);
      }
    }
    if (remote) {
      for (let d of remoteDiff!) {
        keys.push(d.key);
      }
    }
    keys = keys.filter(unique);
    if (local && remote) {
      // Sanity check
      if (localPatch!.key !== remotePatch!.key) {
        throw new Error('Different keys of patch ops given to `splitPatch`.');
      }
    }
    let patchKey = local ? localPatch!.key : remotePatch!.key;
    for (let key of keys) {
      if (this._whitelist && !valueIn(key, this._whitelist)) {
        throw new NotifyUserError('Currently not able to handle decisions on variable \"' +
              key + '\"');
      }
      let el = getDiffEntryByKey(localDiff, key);
      let er = getDiffEntryByKey(remoteDiff, key);
      let onsesided = !(el && er);
      let action: Action = md.action;
      // If one-sided, change 'base' actions to present side
      if (action === 'base' && onsesided) {
        action = el ? 'local' : 'remote';
      }
      // Create new action:
      split.push(new MergeDecision(
        md.absolutePath.concat([patchKey]),
        el ? [el] : null,
        er ? [er] : null,
        action,
        md.conflict));
    }
    let ret = this.splitOnSourceChunks(split);
    resolveCommonPaths(ret);
    return stableSort(ret, decisionSortKey);
  }

  /**
   * Split decisions on 'source' by chunks.
   *
   * This prevents one decision from contributing to more than one chunk.
   */
  protected splitOnSourceChunks(decisions: MergeDecision[]): MergeDecision[] {
    let out: MergeDecision[] = [];
    for (let i=0; i < decisions.length; ++i) {
      let dec = decisions[i];
      if (dec.absolutePath[2] === 'source') {
        let base = this.base!.source;
        if (!Array.isArray(base)) {
          base = splitLines(base);
        }
        dec.level = 3;
        let sub = splitMergeDecisionsOnChunks(base, [dec]);
        resolveCommonPaths(sub);
        out = out.concat(stableSort(sub, decisionSortKey));
      } else {
        out.push(dec);
      }
    }
    return out;
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
