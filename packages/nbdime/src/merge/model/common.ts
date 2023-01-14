// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
'use strict';

import {
  IDiffEntry
} from '../../diff/diffentries';

import {
  DiffRangePos, raw2Pos
} from '../../diff/range';

import {
  StringDiffModel, IStringDiffModel
} from '../../diff/model';

import {
  MergeDecision, buildDiffs, applyDecisions
} from '../../merge/decisions';

import {
   LineChunker, Chunk, labelSource
} from '../../chunking';

import {
  patchStringified, stringifyAndBlankNull
} from '../../patch';

import {
  DeepCopyableObject
} from '../../common/util';



/**
 * A string diff model based on merge decisions.
 */
export
class DecisionStringDiffModel extends StringDiffModel {
  constructor(base: any, decisions: MergeDecision[],
              sourceModels: (IStringDiffModel | null)[],
              collapsible?: boolean, header?: string, collapsed?: boolean) {
    // Set up initial parameters for super call
    let baseStr = stringifyAndBlankNull(base);
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
    let models: (IStringDiffModel | null)[] = [this];
    models = models.concat(this._sourceModels);
    let chunker = new LineChunker();
    let iter = new StringDiffModel.SyncedDiffIter(models);
    for (let v = iter.next(); v !== undefined; v = iter.next()) {
      if (iter.currentModel() === this) {
        // Chunk diffs in own model normally
        // (they should already be present in own model)
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
 * Abstract base class for a merge model of objects of the type ObjectType,
 * which uses DiffModelType to model each side internally.
 *
 * Implementors need to define the abstract functions createDiffModel and
 * createMergedDiffModel.
 */
export
abstract class ObjectMergeModel<ObjectType extends DeepCopyableObject, DiffModelType> {

  /**
   * Create a diff model of the correct type given the diff (which might be
   * null)
   */
  protected abstract createDiffModel(diff: IDiffEntry[] | null): DiffModelType;

  /**
   * Create a diff model of the correct type for the merge
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
  readonly decisions: MergeDecision[];

  /**
   * Apply merge decisions to create the merged cell
   */
  serialize(): ObjectType | null {
    if (this.base === null) {
      return null;
    }
    return applyDecisions(this.base, this.decisions);
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
   * List of fields to handle
   */
  protected _whitelist: string[] | null;

  protected _local?: DiffModelType | null;
  protected _remote?: DiffModelType | null;
  protected _merged?: DiffModelType;

  protected _finalized: boolean = false;
}
