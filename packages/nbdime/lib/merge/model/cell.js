// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
'use strict';
Object.defineProperty(exports, "__esModule", { value: true });
exports.CellMergeModel = void 0;
const nbformat = require("@jupyterlab/nbformat");
const signaling_1 = require("@lumino/signaling");
const util_1 = require("../../diff/util");
const model_1 = require("../../diff/model");
const decisions_1 = require("../../merge/decisions");
const patch_1 = require("../../patch");
const util_2 = require("../../common/util");
const chunking_1 = require("../../chunking");
const common_1 = require("./common");
const exceptions_1 = require("../../common/exceptions");
/**
 * Create a cell diff model based on a set of merge
 * decisions that patch the cell.
 */
function createPatchedCellDecisionDiffModel(base, decisions, local, remote, mimetype) {
    for (let md of decisions) {
        if (md.localPath.length === 0) {
            let val = decisions_1.popPath(md.diffs, true);
            if (val !== null) {
                md.diffs = val.diffs;
                md.pushPath(val.key);
            }
        }
    }
    let source = new common_1.DecisionStringDiffModel(base.source, decisions_1.filterDecisions(decisions, ['source'], 2), [local ? local.source : null,
        remote ? remote.source : null]);
    model_1.setMimetypeFromCellType(source, base, mimetype);
    let metadata = new common_1.DecisionStringDiffModel(base.metadata, decisions_1.filterDecisions(decisions, ['metadata'], 2), [local ? local.metadata : null,
        remote ? remote.metadata : null]);
    let outputs = null;
    let executionCount = null;
    if (nbformat.isCode(base)) {
        if (base.outputs) {
            let outputBase = base.outputs;
            let outputDec = decisions_1.filterDecisions(decisions, ['outputs'], 2);
            let mergedDiff = decisions_1.buildDiffs(outputBase, outputDec, 'merged');
            let merged;
            if (mergedDiff && mergedDiff.length > 0) {
                merged = patch_1.patch(outputBase, mergedDiff);
            }
            else {
                merged = outputBase;
            }
            outputs = model_1.makeOutputModels(outputBase, merged, mergedDiff);
        }
        let execBase = base.execution_count;
        let cellDecs = decisions_1.filterDecisions(decisions, ['cells'], 0, 2);
        for (let dec of cellDecs) {
            if (util_1.getDiffEntryByKey(dec.localDiff, 'execution_count') !== null ||
                util_1.getDiffEntryByKey(dec.remoteDiff, 'execution_count') !== null ||
                util_1.getDiffEntryByKey(dec.customDiff, 'execution_count') !== null) {
                dec.level = 2;
                let mergeExecDiff = decisions_1.buildDiffs(base, [dec], 'merged');
                let execDiff = util_2.hasEntries(mergeExecDiff) ? mergeExecDiff[0] : null;
                // Pass base as remote, which means fall back to unchanged if no diff:
                executionCount = model_1.createImmutableModel(execBase, execBase, execDiff);
            }
        }
    }
    return new model_1.CellDiffModel(source, metadata, outputs, executionCount, base.cell_type);
}
/**
 * CellMergeModel
 */
class CellMergeModel extends common_1.ObjectMergeModel {
    constructor(base, decisions, mimetype) {
        // TODO: Remove/extend whitelist once we support more
        super(base, [], mimetype, ['source', 'metadata', 'outputs', 'execution_count']);
        this.deleteCellChanged = new signaling_1.Signal(this);
        this._clearOutputs = false;
        this.clearOutputsChanged = new signaling_1.Signal(this);
        this.onesided = false;
        this._deleteCell = false;
        this.processDecisions(decisions);
    }
    /**
     * Run time flag whether the user wants to delete the cell
     *
     * @type {boolean}
     */
    get deleteCell() {
        return this._deleteCell;
    }
    set deleteCell(value) {
        if (this._deleteCell !== value) {
            this._deleteCell = value;
            this.deleteCellChanged.emit(value);
        }
    }
    /**
     * Run time flag whether the user wants to clear the outputs of the cell
     *
     * @type {boolean}
     */
    get clearOutputs() {
        return this._clearOutputs;
    }
    set clearOutputs(value) {
        if (this._clearOutputs !== value) {
            this._clearOutputs = value;
            this.clearOutputsChanged.emit(value);
        }
    }
    /**
     * Whether source is the same in local and remote
     */
    get agreedSource() {
        return !!this.local && !!this.remote &&
            this.local.source.remote === this.remote.source.remote;
    }
    /**
     * Whether metadata is the same in local and remote
     */
    get agreedMetadata() {
        if (!this.local || !this.remote) {
            return false;
        }
        return this.local.metadata.remote === this.remote.metadata.remote;
    }
    /**
     * Whether outputs are the same in local and remote
     */
    get agreedOutputs() {
        if (!this.local || !this.remote) {
            return false;
        }
        let lo = this.local.outputs;
        let ro = this.remote.outputs;
        if (!util_2.hasEntries(lo) || !util_2.hasEntries(ro)) {
            return !util_2.hasEntries(lo) && !util_2.hasEntries(ro);
        }
        if (lo.length !== ro.length) {
            return false;
        }
        for (let i = 0; i < lo.length; ++i) {
            if (JSON.stringify(lo[i].remote) !== JSON.stringify(ro[i].remote)) {
                return false;
            }
        }
        return true;
    }
    /**
     * Whether cell is the same in local and remote
     */
    get agreedCell() {
        // TODO: Also check other fields?
        return this.agreedSource && this.agreedMetadata && this.agreedOutputs;
    }
    /**
     * Whether the cell has any conflicted decisions.
     */
    get conflicted() {
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
    hasConflictsOn(key) {
        let decs = decisions_1.filterDecisions(this.decisions, [key], 2);
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
    get sourceConflicted() {
        return this.hasConflictsOn('source');
    }
    /**
     * Whether the cell has any conflicted decisions on metadata.
     */
    get metadataConflicted() {
        return this.hasConflictsOn('metadata');
    }
    /**
     * Whether the cell has any conflicted decisions.
     */
    get outputsConflicted() {
        return this.hasConflictsOn('outputs');
    }
    /**
     * Clear any conflicts on decisions on outputs
     */
    clearOutputConflicts() {
        let decs = decisions_1.filterDecisions(this.decisions, ['outputs'], 2);
        for (let dec of decs) {
            dec.conflict = false;
        }
    }
    /**
     * Get the decision on `execution_count` field (should only be one).
     *
     * Returns null if no decision on `execution_count` was found.
     */
    getExecutionCountDecision() {
        let cellDecs = decisions_1.filterDecisions(this.decisions, ['cells'], 0, 2);
        for (let dec of cellDecs) {
            if (util_1.getDiffEntryByKey(dec.localDiff, 'execution_count') !== null ||
                util_1.getDiffEntryByKey(dec.remoteDiff, 'execution_count') !== null ||
                util_1.getDiffEntryByKey(dec.customDiff, 'execution_count') !== null) {
                return dec;
            }
        }
        return null;
    }
    /**
     * Apply merge decisions to create the merged cell
     */
    serialize() {
        if (this.deleteCell) {
            return null;
        }
        if (this.base === null) {
            // Only possibility is that cell is added
            if (this.decisions.length > 1 || !this.merged.added) {
                throw new exceptions_1.NotifyUserError('Invalid cell decision');
            }
            let dec = this.decisions[0];
            // Either onesided or identical inserts, but possibly with
            // a custom diff on top!
            let d;
            if (dec.action === 'local' || dec.action === 'either') {
                if (!dec.localDiff) {
                    throw new exceptions_1.NotifyUserError('Invalid cell decision');
                }
                d = dec.localDiff[0];
            }
            else if (dec.action === 'remote') {
                if (!dec.remoteDiff) {
                    throw new exceptions_1.NotifyUserError('Invalid cell decision');
                }
                d = dec.remoteDiff[0];
            }
            else if (dec.action === 'custom') {
                if (!dec.customDiff) {
                    throw new exceptions_1.NotifyUserError('Invalid cell decision');
                }
                d = dec.customDiff[0];
            }
            else {
                throw new exceptions_1.NotifyUserError('Invalid cell decision');
            }
            if (d.op !== 'addrange') {
                throw new exceptions_1.NotifyUserError('Invalid cell decision');
            }
            return d.valuelist[0];
        }
        let decisions = [];
        for (let md of this.decisions) {
            let nmd = new decisions_1.MergeDecision(md);
            nmd.level = 2;
            decisions.push(nmd);
        }
        let output = decisions_1.applyDecisions(this.base, decisions);
        let src = output.source;
        if (Array.isArray(src)) {
            src = src.join('');
        }
        if (src !== this._merged.source.remote) {
            console.warn('Serialized outputs doesn\'t match model value! ' +
                'Keeping the model value.');
            output.source = util_2.splitLines(this._merged.source.remote);
        }
        if (this.clearOutputs && nbformat.isCode(output)) {
            output.outputs = [];
        }
        return output;
    }
    processDecisions(decisions) {
        // First check for cell-level decisions:
        if (decisions.length === 1) {
            if (util_2.arraysEqual(decisions[0].absolutePath, ['cells'])) {
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
            }
            else if (md.absolutePath.length === 2 && (util_2.hasEntries(md.localDiff) || util_2.hasEntries(md.remoteDiff))) {
                // Have decision on /cells/X/.
                // Split the decision on subkey:
                // Nest diff as a patch on cell, which can be split by `splitPatch`:
                let splitDec = decisions_1.pushPatchDecision(md, md.absolutePath.slice(1, 2));
                let localDiff = util_2.hasEntries(splitDec.localDiff) ?
                    splitDec.localDiff[0] : null;
                let remoteDiff = util_2.hasEntries(splitDec.remoteDiff) ?
                    splitDec.remoteDiff[0] : null;
                let subDecisions = this.splitPatch(splitDec, localDiff, remoteDiff);
                // Add all split decisions:
                for (let subdec of subDecisions) {
                    subdec.level = 2;
                    this.decisions.push(subdec);
                }
            }
            else { // Decision has path on subkey
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
    applyCellLevelDecision(md) {
        let newDecisions = [];
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
        console.assert(!this.onesided, 'Cannot have multiple cell decisions on one cell!');
        this.onesided = true; // We set this to distinguish case 3 from normal
        if (!util_2.hasEntries(md.localDiff)) {
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
                let v = first.valuelist[0];
                this._remote = model_1.createAddedCellDiffModel(v, this.mimetype);
                this._merged = model_1.createAddedCellDiffModel(v, this.mimetype);
            }
            else {
                // 2.
                this._remote = model_1.createDeletedCellDiffModel(this.base, this.mimetype);
                this._merged = model_1.createDeletedCellDiffModel(this.base, this.mimetype);
                this.deleteCell = util_2.valueIn(md.action, ['remote', 'either']);
            }
        }
        else if (!util_2.hasEntries(md.remoteDiff)) {
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
                let v = first.valuelist[0];
                this._local = model_1.createAddedCellDiffModel(v, this.mimetype);
                this._merged = model_1.createAddedCellDiffModel(v, this.mimetype);
            }
            else {
                // 2.
                this._local = model_1.createDeletedCellDiffModel(this.base, this.mimetype);
                this._merged = model_1.createDeletedCellDiffModel(this.base, this.mimetype);
                this.deleteCell = util_2.valueIn(md.action, ['local', 'either']);
            }
        }
        else {
            console.assert(util_2.hasEntries(md.localDiff) && util_2.hasEntries(md.remoteDiff));
            console.assert(md.localDiff.length === 1 && md.remoteDiff.length === 1);
            // 3. or 4.
            if (md.localDiff[0].op === md.remoteDiff[0].op) {
                // 4.
                if (this.base === null) {
                    // Identical insertions (this relies on preprocessing to ensure only
                    // one value in valuelist)
                    let v = md.localDiff[0].valuelist[0];
                    this._local = model_1.createAddedCellDiffModel(v, this.mimetype);
                    this._remote = model_1.createAddedCellDiffModel(v, this.mimetype);
                    this._merged = model_1.createAddedCellDiffModel(v, this.mimetype);
                }
                else {
                    // Identical delections
                    this._local = model_1.createDeletedCellDiffModel(this.base, this.mimetype);
                    this._remote = model_1.createDeletedCellDiffModel(this.base, this.mimetype);
                    this._merged = model_1.createDeletedCellDiffModel(this.base, this.mimetype);
                    this.deleteCell = util_2.valueIn(md.action, ['local', 'remote', 'either']);
                }
            }
            else {
                // 3., by method of elimination
                let ops = [md.localDiff[0].op, md.remoteDiff[0].op];
                console.assert(util_2.valueIn('removerange', ops) && util_2.valueIn('patch', ops));
                if (this.base === null) {
                    throw new Error('Invalid merge decision, ' +
                        'cannot have null base for deleted cell: ' + md);
                }
                if (ops[0] === 'removerange') {
                    this._local = model_1.createDeletedCellDiffModel(this.base, this.mimetype);
                    this.deleteCell = md.action === 'local';
                    // The patch op will be on cell level. Split it on sub keys!
                    newDecisions = newDecisions.concat(this.splitPatch(md, null, md.remoteDiff[0]));
                }
                else {
                    this._remote = model_1.createDeletedCellDiffModel(this.base, this.mimetype);
                    this.deleteCell = md.action === 'remote';
                    // The patch op will be on cell level. Split it on sub keys!
                    newDecisions = newDecisions.concat(this.splitPatch(md, md.localDiff[0], null));
                }
                decisions_1.resolveCommonPaths(newDecisions);
            }
        }
        return newDecisions;
    }
    /**
     * Split a decision with a patch on one side into one decision
     * for each sub entry in the patch.
     */
    splitPatch(md, localPatch, remotePatch) {
        let local = !!localPatch && util_2.hasEntries(localPatch.diff);
        let remote = !!remotePatch && util_2.hasEntries(remotePatch.diff);
        if (!local && !remote) {
            return [];
        }
        let localDiff = local ? localPatch.diff : null;
        let remoteDiff = remote ? remotePatch.diff : null;
        let split = [];
        let keys = [];
        if (local) {
            for (let d of localDiff) {
                keys.push(d.key);
            }
        }
        if (remote) {
            for (let d of remoteDiff) {
                keys.push(d.key);
            }
        }
        keys = keys.filter(util_2.unique);
        if (local && remote) {
            // Sanity check
            if (localPatch.key !== remotePatch.key) {
                throw new Error('Different keys of patch ops given to `splitPatch`.');
            }
        }
        let patchKey = local ? localPatch.key : remotePatch.key;
        for (let key of keys) {
            if (this._whitelist && !util_2.valueIn(key, this._whitelist)) {
                throw new exceptions_1.NotifyUserError('Currently not able to handle decisions on variable \"' +
                    key + '\"');
            }
            let el = util_1.getDiffEntryByKey(localDiff, key);
            let er = util_1.getDiffEntryByKey(remoteDiff, key);
            let onsesided = !(el && er);
            let action = md.action;
            // If one-sided, change 'base' actions to present side
            if (action === 'base' && onsesided) {
                action = el ? 'local' : 'remote';
            }
            // Create new action:
            split.push(new decisions_1.MergeDecision(md.absolutePath.concat([patchKey]), el ? [el] : null, er ? [er] : null, action, md.conflict));
        }
        let ret = this.splitOnSourceChunks(split);
        decisions_1.resolveCommonPaths(ret);
        return util_2.stableSort(ret, decisions_1.decisionSortKey);
    }
    /**
     * Split decisions on 'source' by chunks.
     *
     * This prevents one decision from contributing to more than one chunk.
     */
    splitOnSourceChunks(decisions) {
        let out = [];
        for (let i = 0; i < decisions.length; ++i) {
            let dec = decisions[i];
            if (dec.absolutePath[2] === 'source') {
                let base = this.base.source;
                if (!Array.isArray(base)) {
                    base = util_2.splitLines(base);
                }
                dec.level = 3;
                let sub = chunking_1.splitMergeDecisionsOnChunks(base, [dec]);
                decisions_1.resolveCommonPaths(sub);
                out = out.concat(util_2.stableSort(sub, decisions_1.decisionSortKey));
            }
            else {
                out.push(dec);
            }
        }
        return out;
    }
    createDiffModel(diff) {
        if (this.base === null) {
            throw new Error('Cannot create a patched or unchanged diff model with null base!');
        }
        if (diff && diff.length > 0) {
            return model_1.createPatchedCellDiffModel(this.base, diff, this.mimetype);
        }
        else {
            return model_1.createUnchangedCellDiffModel(this.base, this.mimetype);
        }
    }
    createMergedDiffModel() {
        if (this.base === null) {
            throw new Error('Cannot create a patched or unchanged merged diff model with null base!');
        }
        return createPatchedCellDecisionDiffModel(this.base, this.decisions, this.local, this.remote, this.mimetype);
    }
}
exports.CellMergeModel = CellMergeModel;
//# sourceMappingURL=cell.js.map