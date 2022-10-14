// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
'use strict';
Object.defineProperty(exports, "__esModule", { value: true });
exports.ObjectMergeModel = exports.DecisionStringDiffModel = void 0;
const range_1 = require("../../diff/range");
const model_1 = require("../../diff/model");
const decisions_1 = require("../../merge/decisions");
const chunking_1 = require("../../chunking");
const patch_1 = require("../../patch");
/**
 * A string diff model based on merge decisions.
 */
class DecisionStringDiffModel extends model_1.StringDiffModel {
    constructor(base, decisions, sourceModels, collapsible, header, collapsed) {
        // Set up initial parameters for super call
        let baseStr = patch_1.stringifyAndBlankNull(base);
        super(baseStr, '', [], [], collapsible, header, collapsed);
        this.rawBase = base;
        this.decisions = decisions;
        this._outdated = true;
        this._sourceModels = sourceModels;
        this._update();
    }
    get additions() {
        if (this._outdated) {
            this._update();
        }
        return this._additions;
    }
    set additions(value) {
        this._additions = value;
    }
    get deletions() {
        if (this._outdated) {
            this._update();
        }
        return this._deletions;
    }
    set deletions(value) {
        this._deletions = value;
    }
    get remote() {
        if (this._outdated) {
            this._update();
        }
        return this._remote;
    }
    set remote(value) {
        this._remote = value;
    }
    invalidate() {
        this._outdated = true;
    }
    get invalid() {
        return this._outdated;
    }
    /**
     * Chunk additions/deletions into line-based chunks, while also producing
     * chunks from source models where the decision is a no-op (action 'base').
     */
    getLineChunks() {
        let models = [this];
        models = models.concat(this._sourceModels);
        let chunker = new chunking_1.LineChunker();
        let iter = new model_1.StringDiffModel.SyncedDiffIter(models);
        for (let v = iter.next(); v !== undefined; v = iter.next()) {
            if (iter.currentModel() === this) {
                // Chunk diffs in own model normally
                // (they should already be present in own model)
                chunker.addDiff(v.range, v.isAddition);
            }
            else {
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
    _update() {
        this._outdated = false;
        let diff = decisions_1.buildDiffs(this.rawBase, this.decisions, 'merged');
        let out = patch_1.patchStringified(this.rawBase, diff);
        this._additions = range_1.raw2Pos(out.additions, out.remote);
        this._deletions = range_1.raw2Pos(out.deletions, this.base || '');
        this._remote = out.remote;
    }
}
exports.DecisionStringDiffModel = DecisionStringDiffModel;
/**
 * Abstract base class for a merge model of objects of the type ObjectType,
 * which uses DiffModelType to model each side internally.
 *
 * Implementors need to define the abstract functions createDiffModel and
 * createMergedDiffModel.
 */
class ObjectMergeModel {
    /**
     *
     */
    constructor(base, decisions, mimetype, whitelist) {
        this._finalized = false;
        this.base = base;
        this.mimetype = mimetype;
        this._whitelist = whitelist || null;
        this.decisions = decisions;
    }
    /**
     * Apply merge decisions to create the merged cell
     */
    serialize() {
        if (this.base === null) {
            return null;
        }
        return decisions_1.applyDecisions(this.base, this.decisions);
    }
    /**
     * Model of the local diff vs. base
     */
    get local() {
        if (this._local === undefined) {
            // We're builiding from decisions
            this._finalizeDecisions();
            let diff = decisions_1.buildDiffs(this.base, this.decisions, 'local');
            this._local = this.createDiffModel(diff);
        }
        return this._local;
    }
    /**
     * Model of the remote diff vs. base
     */
    get remote() {
        if (this._remote === undefined) {
            this._finalizeDecisions();
            let diff = decisions_1.buildDiffs(this.base, this.decisions, 'remote');
            this._remote = this.createDiffModel(diff);
        }
        return this._remote;
    }
    /**
     * Model of the diff of the merged cell vs. base
     */
    get merged() {
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
    get subModels() {
        return [this.local, this.remote, this.merged];
    }
    /**
     * Prevent further changes to decisions, and label the diffs
     *
     * The labels are used for picking of decisions
     */
    _finalizeDecisions() {
        if (!this._finalized) {
            for (let md of this.decisions) {
                if (md.action === 'either') {
                    chunking_1.labelSource(md.localDiff, { decision: md, action: 'either' });
                    chunking_1.labelSource(md.remoteDiff, { decision: md, action: 'either' });
                }
                else {
                    chunking_1.labelSource(md.localDiff, { decision: md, action: 'local' });
                    chunking_1.labelSource(md.remoteDiff, { decision: md, action: 'remote' });
                }
                chunking_1.labelSource(md.customDiff, { decision: md, action: 'custom' });
            }
            this._finalized = true;
        }
    }
}
exports.ObjectMergeModel = ObjectMergeModel;
//# sourceMappingURL=common.js.map