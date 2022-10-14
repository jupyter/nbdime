// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
'use strict';
Object.defineProperty(exports, "__esModule", { value: true });
exports.createDeletedCellDiffModel = exports.createAddedCellDiffModel = exports.createUnchangedCellDiffModel = exports.createPatchedCellDiffModel = exports.CellDiffModel = void 0;
const nbformat = require("@jupyterlab/nbformat");
const exceptions_1 = require("../../common/exceptions");
const util_1 = require("../util");
const string_1 = require("./string");
const output_1 = require("./output");
const immutable_1 = require("./immutable");
/**
 * Diff model for individual Notebook Cells
 */
class CellDiffModel {
    constructor(source, metadata, outputs, executionCount, cellType) {
        this.source = source;
        this.metadata = metadata;
        this.outputs = outputs;
        this.executionCount = executionCount;
        this.cellType = cellType;
        if (outputs === null && cellType === 'code') {
            throw new exceptions_1.NotifyUserError('Invalid code cell, missing outputs!');
        }
        this.metadata.collapsible = true;
        this.metadata.collapsibleHeader = 'Metadata changed';
        this.metadata.startCollapsed = true;
    }
    /**
     * Whether the cell has remained unchanged
     */
    get unchanged() {
        let unchanged = this.source.unchanged;
        unchanged = unchanged &&
            (this.metadata ? this.metadata.unchanged : true);
        if (this.outputs) {
            for (let o of this.outputs) {
                unchanged = unchanged && o.unchanged;
            }
        }
        if (this.executionCount) {
            // TODO: Ignore if option 'ignore minor' set?
            unchanged = unchanged && this.executionCount.unchanged;
        }
        return unchanged;
    }
    /**
     * Whether the cell has been added to the notebook (new cell)
     */
    get added() {
        return this.source.added;
    }
    /**
     * Whether the cell has been deleted/removed from the notebook
     */
    get deleted() {
        return this.source.deleted;
    }
    /**
     * Chunked outputs
     */
    getChunkedOutputs() {
        if (this.outputs === null) {
            return null;
        }
        const chunks = [];
        if (this.added || this.deleted) {
            // Should not chunk outputs for added/deleted cells
            // simply make one element chunks:
            for (let o of this.outputs) {
                chunks.push([o]);
            }
        }
        else {
            let currentChunk = [];
            for (let o of this.outputs) {
                if (o.added || o.deleted) {
                    currentChunk.push(o);
                }
                else {
                    if (currentChunk.length) {
                        chunks.push(currentChunk);
                    }
                    chunks.push([o]);
                    currentChunk = [];
                }
            }
            if (currentChunk.length) {
                chunks.push(currentChunk);
            }
        }
        return chunks;
    }
}
exports.CellDiffModel = CellDiffModel;
function createPatchedCellDiffModel(base, diff, nbMimetype) {
    let source = null;
    let metadata = null;
    let outputs = null;
    let executionCount = null;
    let subDiff = util_1.getSubDiffByKey(diff, 'source');
    if (subDiff) {
        source = string_1.createPatchStringDiffModel(base.source, subDiff);
    }
    else {
        source = string_1.createDirectStringDiffModel(base.source, base.source);
    }
    string_1.setMimetypeFromCellType(source, base, nbMimetype);
    subDiff = util_1.getSubDiffByKey(diff, 'metadata');
    metadata = subDiff ?
        string_1.createPatchStringDiffModel(base.metadata, subDiff) :
        string_1.createDirectStringDiffModel(base.metadata, base.metadata);
    if (nbformat.isCode(base)) {
        let outputsBase = base.outputs;
        let outputsDiff = util_1.getSubDiffByKey(diff, 'outputs');
        if (outputsDiff) {
            // Outputs patched
            outputs = output_1.makeOutputModels(outputsBase, null, outputsDiff);
        }
        else {
            // Outputs unchanged
            outputs = output_1.makeOutputModels(outputsBase, outputsBase);
        }
        let execBase = base.execution_count;
        let execDiff = util_1.getDiffEntryByKey(diff, 'execution_count');
        // Pass base as remote, which means fall back to unchanged if no diff:
        executionCount = immutable_1.createImmutableModel(execBase, execBase, execDiff);
    }
    return new CellDiffModel(source, metadata, outputs, executionCount, base.cell_type);
}
exports.createPatchedCellDiffModel = createPatchedCellDiffModel;
function createUnchangedCellDiffModel(base, nbMimetype) {
    let source = string_1.createDirectStringDiffModel(base.source, base.source);
    string_1.setMimetypeFromCellType(source, base, nbMimetype);
    let metadata = string_1.createDirectStringDiffModel(base.metadata, base.metadata);
    let outputs = null;
    let executionCount = null;
    if (nbformat.isCode(base)) {
        outputs = output_1.makeOutputModels(base.outputs, base.outputs);
        let execBase = base.execution_count;
        executionCount = immutable_1.createImmutableModel(execBase, execBase);
    }
    else { // markdown or raw cell
    }
    return new CellDiffModel(source, metadata, outputs, executionCount, base.cell_type);
}
exports.createUnchangedCellDiffModel = createUnchangedCellDiffModel;
function createAddedCellDiffModel(remote, nbMimetype) {
    let source = string_1.createDirectStringDiffModel(null, remote.source);
    string_1.setMimetypeFromCellType(source, remote, nbMimetype);
    let metadata = string_1.createDirectStringDiffModel(null, remote.metadata);
    let outputs = null;
    let executionCount = null;
    if (nbformat.isCode(remote)) {
        outputs = output_1.makeOutputModels(null, remote.outputs);
        executionCount = immutable_1.createImmutableModel(null, remote.execution_count);
    }
    return new CellDiffModel(source, metadata, outputs, executionCount, remote.cell_type);
}
exports.createAddedCellDiffModel = createAddedCellDiffModel;
function createDeletedCellDiffModel(base, nbMimetype) {
    let source = string_1.createDirectStringDiffModel(base.source, null);
    string_1.setMimetypeFromCellType(source, base, nbMimetype);
    let metadata = string_1.createDirectStringDiffModel(base.metadata, null);
    let outputs = null;
    let executionCount = null;
    if (nbformat.isCode(base)) {
        outputs = output_1.makeOutputModels(base.outputs, null);
        let execBase = base.execution_count;
        executionCount = immutable_1.createImmutableModel(execBase, null);
    }
    return new CellDiffModel(source, metadata, outputs, executionCount, base.cell_type);
}
exports.createDeletedCellDiffModel = createDeletedCellDiffModel;
//# sourceMappingURL=cell.js.map