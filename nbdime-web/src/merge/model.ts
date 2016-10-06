// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
'use strict';

import {
  nbformat
} from 'jupyterlab/lib/notebook/notebook/nbformat';

import {
  IDiffAddRange, IDiffPatch, IDiffRemoveRange, IDiffEntry
} from '../diff/diffentries';

import {
  DiffRangePos, raw2Pos
} from '../diff/range';

import {
  CellDiffModel, createAddedCellDiffModel, StringDiffModel, IStringDiffModel,
  createDeletedCellDiffModel, createPatchedCellDiffModel,
  createUnchangedCellDiffModel, setMimetypeFromCellType, OutputDiffModel,
  makeOutputModels, createPatchDiffModel, createDirectDiffModel
} from '../diff/model';

import {
  IMergeDecision, MergeDecision, resolveCommonPaths, buildDiffs,
  filterDecisions, pushPatchDecision, popPath, applyDecisions, Action
} from '../merge/decisions';

import {
   LineChunker, Chunk, labelSource
} from '../chunking';

import {
  stringify, patchStringified, patch
} from '../patch';

import {
  arraysEqual, valueIn, hasEntries
} from '../common/util';


/**
 * A string diff model based on merge decisions.
 */
export
class DecisionStringDiffModel extends StringDiffModel {
  constructor(base: any, decisions: MergeDecision[],
              sourceModels: (IStringDiffModel | null)[],
              collapsible?: boolean, header?: string, collapsed?: boolean) {
    // Set up initial parameters for super call
    let baseStr = (typeof base === 'string') ? base as string : stringify(base);
    super(baseStr, '', [], [],
      collapsible, header, collapsed);
    this.rawBase = base;
    this.decisions = decisions;
    this._outdated = true;
    this._sourceModels = sourceModels;
    this._update();
  }

  decisions: MergeDecision[];

  rawBase: any;

  get additions(): DiffRangePos[] {
    if (this._outdated) {
      this._update();
    }
    return this._additions;
  }
  set additions(value: DiffRangePos[]) {
    this._additions = value;
  }

  get deletions(): DiffRangePos[] {
    if (this._outdated) {
      this._update();
    }
    return this._deletions;
  }
  set deletions(value: DiffRangePos[]) {
    this._deletions = value;
  }

  get remote(): string {
    if (this._outdated) {
      this._update();
    }
    return this._remote;
  }
  set remote(value: string) {
    this._remote = value;
  }

  invalidate() {
    this._outdated = true;
  }

  get invalid(): boolean {
    return this._outdated;
  }

  /**
   * Chunk additions/deletions into line-based chunks, while also producing
   * chunks from source models where the decision is a no-op (action 'base').
   */
  getLineChunks(): Chunk[] {
    let models: (IStringDiffModel | null)[] = [this as IStringDiffModel];
    models = models.concat(this._sourceModels);
    let chunker = new LineChunker();
    let iter = new StringDiffModel.SyncedDiffIter(models);
    for (let v = iter.next(); v !== undefined; v = iter.next()) {
      if (iter.currentModel() === this) {
        // Chunk diffs in own model normally
        chunker.addDiff(v.range, v.isAddition);
      } else {
        // Skip ops in other models that are not no-ops
        if (!v.range.source || v.range.source.decision.action !== 'base') {
          continue;
        }
        // Other model
        chunker.addGhost(v.range, v.isAddition, iter.currentOffset);
      }
    }
    return chunker.chunks;
  }

  protected _update(): void {
    this._outdated = false;
    let diff = buildDiffs(this.rawBase, this.decisions, 'merged');
    let out = patchStringified(this.rawBase, diff);
    this._additions = raw2Pos(out.additions, out.remote);
    this._deletions = raw2Pos(out.deletions, this.base || '');
    this._remote = out.remote;
  }

  protected _additions: DiffRangePos[];
  protected _deletions: DiffRangePos[];
  protected _remote: string;
  protected _outdated: boolean;
  protected _sourceModels: (IStringDiffModel | null)[];
}


/**
 * Create a cell diff model based on a set of merge
 * decisions that patch the cell.
 */
function createPatchedCellDecisionDiffModel(
    base: nbformat.ICell, decisions: MergeDecision[],
    mimetype: string,
    local: CellDiffModel | null, remote: CellDiffModel | null):
    CellDiffModel {

  for (let md of decisions) {
    if (md.localPath.length === 0) {
      let val = popPath(md.diffs, true);
      if (val === null) {
        throw 'Invalid diffs for patching cell!';
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
    let mergedDiff = buildDiffs(outputBase, outputDec, 'merged');
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
 * Abstract base class for a merge model of objects of the type ObjectType,
 * which uses DiffModelType to model each side internally.
 *
 * Implementors need to define the abstract functions createDiffModel and
 * createMergedDiffModel.
 */
export
abstract class ObjectMergeModel<ObjectType, DiffModelType> {

  /**
   * Create a diff model of the correct type given the diff (which might be
   * null)
   */
  protected abstract createDiffModel(diff: IDiffEntry[] | null): DiffModelType;

  /**
   * Create a diff model of the correct type for the merge given the diff
   */
  protected abstract createMergedDiffModel(): DiffModelType;

  /**
   *
   */
  constructor(base: ObjectType | null, decisions: MergeDecision[], mimetype: string,
              whitelist?: string[]) {
    this.base = base;
    this.mimetype = mimetype;
    this._whitelist = whitelist || null;

    this.decisions = decisions;
  }

  /**
   * Base value of the object
   */
  base: ObjectType | null;

  /**
   * The mimetype to use for the source
   */
  mimetype: string;

  /**
   * The merge decisions that apply to this object
   */
  decisions: MergeDecision[];

  /**
   * Apply merge decisions to create the merged cell
   */
  serialize(): ObjectType {
    return applyDecisions(this.base, this.decisions) as ObjectType;
  }

  /**
   * Model of the local diff vs. base
   */
  get local(): DiffModelType | null {
    if (this._local === undefined) {
      // We're builiding from decisions
      this._finalizeDecisions();
      let diff = buildDiffs(this.base, this.decisions, 'local');
      this._local = this.createDiffModel(diff);
    }
    return this._local;
  }

  /**
   * Model of the remote diff vs. base
   */
  get remote(): DiffModelType | null {
    if (this._remote === undefined) {
      this._finalizeDecisions();
      let diff = buildDiffs(this.base, this.decisions, 'remote');
      this._remote = this.createDiffModel(diff);
    }
    return this._remote;
  }

  /**
   * Model of the diff of the merged cell vs. base
   */
  get merged(): DiffModelType {
    if (this._merged === undefined) {
      this._finalizeDecisions();
      // Merge model needs access to local and remote models to also include
      // chunks from them
      this._merged = this.createMergedDiffModel();
    }
    return this._merged;
  }

  /**
   *
   */
  get subModels(): [DiffModelType | null, DiffModelType | null, DiffModelType] {
    return [this.local, this.remote, this.merged];
  }

  /**
   * Prevent further changes to decisions, and label the diffs
   *
   * The labels are used for picking of decisions
   */
  protected _finalizeDecisions(): void {
    if (!this._finalized) {
      for (let md of this.decisions) {
        if (md.action === 'either') {
          labelSource(md.localDiff, {decision: md, action: 'either'});
          labelSource(md.remoteDiff, {decision: md, action: 'either'});
        } else {
          labelSource(md.localDiff, {decision: md, action: 'local'});
          labelSource(md.remoteDiff, {decision: md, action: 'remote'});
        }
        labelSource(md.customDiff, {decision: md, action: 'custom'});
      }
      this._finalized = true;
    }
  }


  /**
   * Split a decision with a patch on one side into a set of new, one-sided
   * patch opertations. Useful to split a deletion vs patch decision.
   */
  protected splitPatch(md: MergeDecision, patch: IDiffPatch, local: boolean): MergeDecision[] {
    // Split patch on source, metadata and outputs, and make new decisions
    let diff = patch.diff;
    if (!diff) {
      return [];
    }
    let out: MergeDecision[] = [];
    for (let d of diff) {
      if (this._whitelist && !valueIn(d.key, this._whitelist)) {
        throw 'Currently not able to handle decisions on variable \"' +
              d.key + '\"';
      }
      let action: Action = (md.action === 'base' ?
        local ? 'local' : 'remote' :
        md.action);
      out.push(new MergeDecision(
        md.absolutePath.concat([patch.key]),
        local ? [d] : null,
        local ? null : [d],
        action,
        md.conflict));
    }
    return out;
  }

  /**
   * List of fields to handle
   */
  protected _whitelist: string[] | null;

  protected _local?: DiffModelType | null;
  protected _remote?: DiffModelType | null;
  protected _merged?: DiffModelType;

  protected _finalized: boolean = false;
}


/**
 * CellMergeModel
 */
export class CellMergeModel extends ObjectMergeModel<nbformat.ICell, CellDiffModel> {
  constructor(base: nbformat.ICell | null, decisions: MergeDecision[], mimetype: string) {
    // TODO: Remove/extend whitelist once we support more
    super(base, decisions, mimetype, ['source', 'metadata', 'outputs']);
    this.onesided = false;
    this.deleteCell = false;

    // First check for cell-level decisions:
    if (decisions.length === 1 &&
        arraysEqual(decisions[0].absolutePath, ['cells'])) {
      // We have a cell level decision
      let md = decisions[0];
      decisions = this._applyCellDecision(md);
    }
    this.decisions = [];
    for (let md of decisions) {
      // Make local path relative to cell
      md.level = 2;
      this.decisions.push(md);
    }
  }

  /**
   * Whether the cell is present in only one of the two side (local/remote)
   */
  onesided: boolean;

  /**
   * Run time flag whether the user wants to delete the cell or not
   */
  deleteCell: boolean;

  get agreedSource(): boolean {
    return !!this.local && !!this.remote &&
      this.local.source.remote === this.remote.source.remote;
  }

  get agreedMetadata(): boolean {
    if (!this.local || !this.remote) {
      return false;
    }
    return this.local.metadata.remote === this.remote.metadata.remote;
  }

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

  get agreedCell(): boolean {
    return this.agreedSource && this.agreedMetadata && this.agreedOutputs;
  }

  /**
   *
   */
  addDecision(decision: MergeDecision) {
    // Don't allow additional decision if we've already made models!
    if (this._local || this._remote || this._merged) {
      if (this._finalized) {
        throw 'Cannot add a decision to a finalized cell merge model';
      } else {
        throw 'Cannot add more than one cell level decision to one cell';
      }
    } else if (decision.absolutePath.length < 1 ||
               decision.absolutePath[0] !== 'cells') {
      throw 'Not a valid path for a cell decision';
    }

    // Check if descision is on cell level or not:
    if (arraysEqual(decision.absolutePath, ['cells']) ) {
      // Cell level decision (addrange/removerange):
      let decisions = this._applyCellDecision(decision);
      // Add transformed decisions to model:
      for (let md of decisions) {
        md.level = 2;
        this.decisions.push(md);
      }
    } else if (decision.absolutePath.length === 2 && (
        hasEntries(decision.localDiff) || hasEntries(decision.remoteDiff))) {
      if (hasEntries(decision.localDiff) && hasEntries(decision.remoteDiff)) {
        throw 'Invalid merge decision: ' + decision;
      }
      // More than one diff op on cell level, split decisions on key
      // Translate decision to format taken by _splitPatch, and apply:
      decision = pushPatchDecision(decision, decision.absolutePath.slice(1, 2));
      let diff = ((hasEntries(decision.localDiff) ?
        decision.localDiff : decision.remoteDiff) as IDiffPatch[])[0];
      let decisions = this.splitPatch(decision, diff,
                                      hasEntries(decision.localDiff));
      resolveCommonPaths(decisions);
      for (let md of decisions) {
        md.level = 2;
        this.decisions.push(md);
      }
    } else {
      // Either single diff op on cell level, or a decision on a subpath
      // Valid path assured by above tests
      decision.level = 2;
      this.decisions.push(decision);
    }
  }

  /**
   * Apply merge decisions to create the merged cell
   */
  serialize(): nbformat.ICell {
    let decisions: MergeDecision[] = [];
    for (let md of this.decisions) {
      let nmd = new MergeDecision(md);
      nmd.level = 2;
      decisions.push(nmd);
    }
    return applyDecisions(this.base, decisions) as nbformat.ICell;
  }

  protected createDiffModel(diff: IDiffEntry[]): CellDiffModel {
    if (this.base === null) {
      throw 'Cannot create a patched or unchanged diff model with null base!';
    }
    if (diff && diff.length > 0) {
      return createPatchedCellDiffModel(this.base, diff, this.mimetype);
    } else {
      return createUnchangedCellDiffModel(this.base, this.mimetype);
    }
  }

  protected createMergedDiffModel(): CellDiffModel {
    if (this.base === null) {
      throw 'Cannot create a patched or unchanged merged diff model with null base!';
    }
    return createPatchedCellDecisionDiffModel(
        this.base, this.decisions, this.mimetype, this.local, this.remote);
  }

  /**
   * Apply a cell level decision to the model
   *
   * This creates the revelant kinds of models
   */
  protected _applyCellDecision(md: MergeDecision): MergeDecision[] {
    let newDecisions: MergeDecision[] = [];
    /* Possibilities:
     1. Insertion: base is null! Null diff of missing side (unchanged).
     2. Deletion: Null diff of present side (unchanged). Set deleteCell
        depending on action.
     3. Deletion vs patch: Same as 2., but split patch decision onto
        source/metadata/outputs.
     4. Identical ops (insertion or deletion)
     Cases that shouldn't happen:
     5. Insertion vs insertion: Shouldn't happen! Caller should split into
        two decisions with an insertion each
     6. Patch vs patch: Shouldn't occur, as those should have been recursed
     */
    console.assert(!this.onesided,
                   'Cannot have multiple cell decisions on one cell!');
    this.onesided = true;  // We set this to distinguish case 3 from normal
    if (!hasEntries(md.localDiff)) {
      // 1. or 2.:
      this._local = null;
      if (!md.remoteDiff || md.remoteDiff.length !== 1) {
        throw 'Merge decision does not conform to expectation: ' + md;
      }
      if (this.base === null) {
        // 1.
        console.assert(md.remoteDiff[0].op === 'addrange');
        let v = (md.remoteDiff[0] as IDiffAddRange).valuelist[0];
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
        throw 'Merge decision does not conform to expectation: ' + md;
      }
      if (this.base === null) {
        // 1.
        console.assert(md.localDiff[0].op === 'addrange');
        let v = (md.localDiff[0] as IDiffAddRange).valuelist[0];
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
          throw 'Invalid merge decision, ' +
            'cannot have null base for deleted cell: ' + md;
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
      }
    }
    return newDecisions;
  }
}


/**
 * Model of a merge of metadata with decisions
 */
export
class MetadataMergeModel extends ObjectMergeModel<nbformat.INotebookMetadata, IStringDiffModel> {
  constructor(base: nbformat.INotebookMetadata, decisions: MergeDecision[], mimetype: string) {
    super(base, decisions, mimetype);
  }

  protected createDiffModel(diff: IDiffEntry[]): IStringDiffModel {
    if (diff && diff.length > 0) {
      return createPatchDiffModel(this.base, diff);
    } else {
      return createDirectDiffModel(this.base, this.base);
    }
  }

  protected createMergedDiffModel(): IStringDiffModel {
    return new DecisionStringDiffModel(
      this.base, this.decisions,
      [this.local, this.remote]);
  }
}



/**
 * The merge format allows for chunking of sequence diffs such that one entry
 * in the diff lists have 2 entries, where the first is always an insertion
 * (addrange). For cells, we split these decisions in two, for easier
 * visualization.
 */
function splitCellChunks(mergeDecisions: MergeDecision[]): MergeDecision[] {
  let output: MergeDecision[] = [];
  for (let md of mergeDecisions) {
    if (arraysEqual(md.absolutePath, ['cells'])) {
      if (md.localDiff && !md.remoteDiff) {
        for (let d of md.localDiff) {
          let nmd = new MergeDecision(md);
          nmd.localDiff = [d];
          output.push(nmd);
        }
      } else if (md.remoteDiff && !md.localDiff) {
        for (let d of md.remoteDiff) {
          let nmd = new MergeDecision(md);
          nmd.absolutePath = md.absolutePath.slice();
          nmd.remoteDiff = [d];
          output.push(nmd);
        }
      } else if (md.localDiff && md.localDiff.length === 2) {
        // Split off local
        output.push(new MergeDecision(
          md.absolutePath.slice(),
          md.localDiff.slice(0, 1),
          [],
          'local', // Check for custom action first?
          md.conflict
        ));
        let nmd = new MergeDecision(md);
        nmd.localDiff = md.localDiff.slice(1);
        output.push(nmd);
      } else if (md.remoteDiff && md.remoteDiff.length === 2) {
        // Split off remote
        output.push(new MergeDecision(
          md.absolutePath.slice(),
          [],
          md.remoteDiff.slice(0, 1),
          'remote', // Check for custom action first?
          md.conflict
        ));
        let nmd = new MergeDecision(md);
        nmd.remoteDiff = md.remoteDiff.slice(1);
        output.push(nmd);
      } else {
        output.push(md);  // deepCopy?
      }
    } else {
      output.push(md);
    }
  }
  resolveCommonPaths(output);
  return output;
}


/**
 * Split "removerange" diffs on cell list level into individual decisions!
 */
function splitCellRemovals(mergeDecisions: MergeDecision[]): MergeDecision[] {
  let output: MergeDecision[] = [];

  let makeSplitPart = function(md: MergeDecision, key: number,
                               local: boolean, remote: boolean): MergeDecision {
    let newMd = new MergeDecision(md.absolutePath.slice(), null, null,
                                  md.action, md.conflict);
    let newDiff: IDiffRemoveRange[] = [{
        key: key,
        op: 'removerange',
        length: 1
    }];
    console.assert(local || remote);
    if (local) {
      newMd.localDiff = newDiff;
    }
    if (remote) {
      newMd.remoteDiff = newDiff;
    }
    return newMd;
  };

  for (let md of mergeDecisions) {
    if (!arraysEqual(md.absolutePath, ['cells'])) {
      output.push(md);
      continue;
    }

    let dl = hasEntries(md.localDiff) ? md.localDiff[md.localDiff.length - 1] : null;
    let dr = hasEntries(md.remoteDiff) ? md.remoteDiff[md.remoteDiff.length - 1] : null;
    // TODO: Does it make sense to split on custom?

    if (dl && !dr || dr && !dl) {
      // One-way diff
      let d = (dl ? dl : dr) as IDiffEntry;

      if (d.op === 'removerange' && (d as IDiffRemoveRange).length > 1) {
        // Found a one-way diff to split!
        for (let i = 0; i < (d as IDiffRemoveRange).length; ++i) {
          output.push(makeSplitPart(md, (d.key as number) + i, !!dl, !!dr));
        }
      } else {
        // Not a removerange type:
        output.push(md);
        continue;
      }
    } else if (dr && dl) {
      // Two way diff, keys need to be matched
      if (dl.op !== 'removerange' && dr.op !== 'removerange') {
        // Not a removerange type:
        output.push(md);
        continue;
      } else if (dl.op === dr.op) {
        // Both sides have removerange, just match keys/length
        // Note: Assume that ranges have overlap, since they are in one decision
        let klStart = dl.key as number;
        let krStart = dr.key as number;
        let start = Math.min(klStart, krStart);
        let klEnd = klStart + (dl as IDiffRemoveRange).length;
        let krEnd = krStart + (dr as IDiffRemoveRange).length;
        let end = Math.max(klEnd, krEnd);
        for (let i = start; i < end; ++i) {
          let local = i >= klStart && i < klEnd;
          let remote = i >= krStart && i < krEnd;
          output.push(makeSplitPart(md, i, local, remote));
        }
      } else {
        // One side has removerange, the other a patch op (implied)
        let remLocal = dl.op === 'removerange';
        let rOp = (remLocal ? dl : dr) as IDiffRemoveRange;
        let pOp = (remLocal ? dr : dl) as IDiffPatch;
        console.assert(pOp.op === 'patch');

        let pidx = pOp.key as number;
        let start = rOp.key as number;
        for (let i = start; i < start + rOp.length; ++i) {
          let newMd = makeSplitPart(md, i, remLocal, !remLocal);
          if (i === pidx) {
            if (remLocal) {
              newMd.remoteDiff = [pOp];
            } else  {
              newMd.localDiff = [pOp];
            }
          }
          output.push(newMd);
        }
      }
    }
  }
  return output;
}


/**
 * Split "addrange" diffs on cell list level into individual decisions!
 * Also splits two-way insertions into two individual ones.
 */
function splitCellInsertions(mergeDecisions: MergeDecision[]): MergeDecision[] {
  let output: MergeDecision[] = [];

  let makeSplitPart = function(md: MergeDecision, value: any,
                               local: boolean, remote: boolean): MergeDecision {
    let newMd = new MergeDecision(md.absolutePath.slice(), null, null,
                                  md.action, md.conflict);
    if ((local && !hasEntries(md.localDiff)) || !hasEntries(md.remoteDiff)) {
      throw 'Invalid input: ' + md;
    }
    let key = (local ? md.localDiff : md.remoteDiff)![0].key;
    let newDiff: IDiffAddRange[] = [{
        key: key as number,
        op: 'addrange',
        valuelist: [value]
    }];

    console.assert(local || remote);
    if (local) {
      newMd.localDiff = newDiff;
    }
    if (remote) {
      newMd.remoteDiff = newDiff;
    }
    return newMd;
  };

  for (let md of mergeDecisions) {
    // Just push decisions not on cells list:
    if (!arraysEqual(md.absolutePath, ['cells'])) {
      output.push(md);
      continue;
    }

    // Check wether all diffs are pure addrange
    let correctType = true;
    if (md.localDiff) {
      for (let dl of md.localDiff) {
        if (dl.op !== 'addrange') {
          correctType = false;
          break;
        }
      }
    }
    if (md.remoteDiff) {
      for (let dl of md.remoteDiff) {
        if (dl.op !== 'addrange') {
          correctType = false;
          break;
        }
      }
    }
    if (!correctType) {
      output.push(md);
      continue;
    }

    let dl = md.localDiff && md.localDiff.length === 1 ? md.localDiff[0]  as IDiffAddRange : null;
    let dr = md.remoteDiff && md.remoteDiff.length === 1 ? md.remoteDiff[0] as IDiffAddRange : null;

    if (dl && !dr || dr && !dl) {
      // One-way diff
      let d = (dl ? dl : dr) as IDiffAddRange;
      let insert = d.valuelist;
      for (let v of insert) {
        output.push(makeSplitPart(md, v, !!dl, !!dr));
      }
    } else if (dl && dr) {
      // Two way diff
      // First, check if both insertions are equal!
      let eq = stringify(dl.valuelist) === stringify(dr.valuelist);
      if (eq) {
        // Split to one decision per cell
        for (let c of dl.valuelist) {
          output.push(makeSplitPart(md, c, true, true));
        }
      } else {
        // Next, check decision for ruling on order (e.g.
        // local_then_remote, which we will use as the default).

        let start = dl.key as number;
        console.assert(start === dr.key);
        if (md.action === 'remote_then_local') {
          // Only case where we need to switch order!
          for (let c of dr.valuelist as any[]) {
            output.push(makeSplitPart(md, c, false, true));
          }
          for (let c of dl.valuelist as any[]) {
            output.push(makeSplitPart(md, c, true, false));
          }
        } else {
          for (let c of dl.valuelist as any[]) {
            output.push(makeSplitPart(md, c, true, false));
          }
          for (let c of dr.valuelist as any[]) {
            output.push(makeSplitPart(md, c, false, true));
          }
        }
      }

    }
  }
  return output;
}


/**
 * Diff model for a Jupyter Notebook
 */
export
class NotebookMergeModel {

  static preprocessDecisions(rawMergeDecisions: IMergeDecision[]): MergeDecision[] {
    let mergeDecisions: MergeDecision[] = [];
    for (let rmd of rawMergeDecisions) {
      mergeDecisions.push(new MergeDecision(rmd));
    }
    mergeDecisions = splitCellChunks(mergeDecisions);
    mergeDecisions = splitCellRemovals(mergeDecisions);
    mergeDecisions = splitCellInsertions(mergeDecisions);
    resolveCommonPaths(mergeDecisions);
    for (let md of mergeDecisions) {
      if (md.action === 'either') {
        labelSource(md.localDiff, {decision: md, action: 'either'});
        labelSource(md.remoteDiff, {decision: md, action: 'either'});
      } else {
        labelSource(md.localDiff, {decision: md, action: 'local'});
        labelSource(md.remoteDiff, {decision: md, action: 'remote'});
      }
      labelSource(md.customDiff, {decision: md, action: 'custom'});
    }
    return mergeDecisions;
  }

  /**
   * Create a new NotebookDiffModel from a base notebook and a list of diffs.
   *
   * The base as well as the diff entries are normally supplied by the nbdime
   * server.
   */
  constructor(base: nbformat.INotebookContent,
              rawMergeDecisions: IMergeDecision[]) {
    this.base = base;
    let ctor = this.constructor as typeof NotebookMergeModel;
    let decisions = ctor.preprocessDecisions(rawMergeDecisions);

    // The notebook metadata MIME type is used for determining the MIME type
    // of source cells, so store it easily accessible:
    let mimetype: string | undefined;
    try {
      mimetype = base.metadata.language_info.mimetype;
    } catch (e) {
      // missing metadata(probably old notebook)
    }
    this.mimetype = mimetype || 'text/python';

    this.cells = this.buildCellList(decisions);

    let metadataDecs = filterDecisions(decisions, ['metadata']);
    if (metadataDecs.length > 0) {
      this.metadata = new MetadataMergeModel(base.metadata, metadataDecs,
        this.mimetype);
    }
    this.unsavedChanges = false;
  }


  serialize(): nbformat.INotebookContent {
    let nb = {};
    // Simply copy all root-level fields except cells/metadata
    for (let key in this.base) {
      if (!valueIn(key, ['cells', 'metadata'])) {
        nb[key] = this.base[key];
      }
    }

    // Serialize metadata
    nb['metadata'] = this.metadata.serialize();

    // Serialzie cell list
    let cells: nbformat.ICell[] = [];
    for (let c of this.cells) {
      cells.push(c.serialize());
    }
    nb['cells'] = cells;

    // As long as base is a valid notebook, and sub-serialization is valid,
    // this output should be a valid notebook.
    return nb as nbformat.INotebookContent;
  }

  decisions(): MergeDecision[] {
    let ret: MergeDecision[] = [];
    for (let c of this.cells) {
      ret = ret.concat(c.decisions);
    }
    return ret;
  }

  conflicts(): MergeDecision[] {
    let ret: MergeDecision[] = [];
    for (let md of this.decisions()) {
      if (md.conflict) {
        ret.push(md);
      }
    }
    return ret;
  }

  /**
   * Base notebook of the merge
   */
  base: nbformat.INotebookContent;

  /**
   * List of individual cell merges
   */
  cells: CellMergeModel[];

  /**
   * Metadata merge model
   */
  metadata: MetadataMergeModel;

  /**
   * The default MIME type according to the notebook's root metadata
   */
  mimetype: string;

  /**
   * Whether there are unsaved changes
   */
  unsavedChanges: boolean;

  /**
   * Correlate the different cells in the diff lists into a merge list
   */
  protected buildCellList(decisions: MergeDecision[]): CellMergeModel[] {
    // We have to check for merge decisions on the `cells` object in
    // order to check for added cells. This assumes that the common
    // paths of the merge decisions have been resolved. It also assumes that
    // no merge decision can have root as its common path.

    let cells: CellMergeModel[] = [];

    // Simply create unchanged cells first, then we will modify as neccessary
    // below.
    for (let bc of this.base.cells) {
      cells.push(new CellMergeModel(bc, [], this.mimetype));
    }

    let insertOffset = 0;
    // Assumes merge decisions come in order!
    for (let md of decisions) {
      let key = md.absolutePath;
      if (key.length < 1 || key[0] !== 'cells') {
        continue;   // Only care about decisions on cells here
      }

      if (arraysEqual(key, ['cells'])) {
        let idx: number | null = null;
        let insertion = false;
        for (let di of md.diffs) {
          // Ensure diff has exactly one item:
          if (!di || di.length === 0) {
            continue;
          }
          // All keys should be the same since we run splitCellChunks first
          idx = (di[0].key as number);
          if (di[0].op === 'addrange') {
            // Rely on preprocessing splitting to cell level!
            let insertedCell = new CellMergeModel(null, [md], this.mimetype);

            // Insert entries into `cells` at idx
            let offsetIdx = insertOffset + idx;
            cells.splice(offsetIdx, 0, insertedCell);
            insertOffset += 1;
            insertion = true;  // flag to break outer loop
            break;
          }
          // Only checking for insertions in this loop, since insertions can
          // only be paired with other insertions.
        }
        if (insertion) {
          continue;
        }
        // If we reach this point, it is not an insertion merge!
        if (idx === null) {
          throw 'No index could be found for merge decision!';
        }
        let c = cells[idx + insertOffset];
        c.addDecision(md);
      } else {
        // Has a path into a cell
        // Format specifies that these always comes before decisions that
        // change the order of cells, so index is straight forward!
        let idx = key[1];
        let c = cells[idx];
        c.addDecision(md);
      }
    }

    return cells;
  }
}
