// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
'use strict';
Object.defineProperty(exports, "__esModule", { value: true });
exports.NotebookDiffModel = void 0;
const util_1 = require("../util");
const string_1 = require("./string");
const cell_1 = require("./cell");
/**
 * Diff model for a Jupyter Notebook
 */
class NotebookDiffModel {
    /**
     * Create a new NotebookDiffModel from a base notebook and a list of diffs.
     *
     * The base as well as the diff entries are normally supplied by the nbdime
     * server.
     */
    constructor(base, diff) {
        // Process global notebook metadata field
        let metaDiff = util_1.getSubDiffByKey(diff, 'metadata');
        if (base.metadata && metaDiff) {
            this.metadata = string_1.createPatchStringDiffModel(base.metadata, metaDiff);
        }
        else {
            this.metadata = null;
        }
        if (this.metadata) {
            this.metadata.collapsible = true;
            this.metadata.collapsibleHeader = 'Notebook metadata changed';
            this.metadata.startCollapsed = true;
        }
        // The notebook metadata MIME type is used for determining the MIME type
        // of source cells, so store it easily accessible:
        let mimetype;
        try {
            mimetype = base.metadata.language_info.mimetype;
        }
        catch (e) {
            // missing metadata (probably old notebook)
        }
        this.mimetype = mimetype || 'text/python';
        // Build cell diff models. Follows similar logic to patching code:
        this.cells = [];
        this.chunkedCells = [];
        let take = 0;
        let skip = 0;
        let previousChunkIndex = -1;
        let currentChunk = [];
        for (let e of util_1.getSubDiffByKey(diff, 'cells') || []) {
            let index = e.key;
            // diff is sorted on index, so take any preceding cells as unchanged:
            for (let i = take; i < index; i++) {
                let cell = cell_1.createUnchangedCellDiffModel(base.cells[i], this.mimetype);
                this.cells.push(cell);
                this.chunkedCells.push([cell]);
            }
            if (index !== previousChunkIndex) {
                currentChunk = [];
                this.chunkedCells.push(currentChunk);
                previousChunkIndex = index;
            }
            // Process according to diff type:
            if (e.op === 'addrange') {
                // One or more inserted/added cells:
                for (let ei of e.valuelist) {
                    let cell = cell_1.createAddedCellDiffModel(ei, this.mimetype);
                    this.cells.push(cell);
                    currentChunk.push(cell);
                }
                skip = 0;
            }
            else if (e.op === 'removerange') {
                // One or more removed/deleted cells:
                skip = e.length;
                for (let i = index; i < index + skip; i++) {
                    let cell = cell_1.createDeletedCellDiffModel(base.cells[i], this.mimetype);
                    this.cells.push(cell);
                    currentChunk.push(cell);
                }
            }
            else if (e.op === 'patch') {
                // Ensure patches gets their own chunk, even if they share index:
                if (currentChunk.length > 0) {
                    currentChunk = [];
                    this.chunkedCells.push(currentChunk);
                }
                // A cell has changed:
                let cell = cell_1.createPatchedCellDiffModel(base.cells[index], e.diff, this.mimetype);
                this.cells.push(cell);
                currentChunk.push(cell);
                skip = 1;
            }
            // Skip the specified number of elements, but never decrement take.
            // Note that take can pass index in diffs with repeated +/- on the
            // same index, i.e. [op_remove(index), op_add(index, value)]
            take = Math.max(take, index + skip);
        }
        // Take unchanged values at end
        for (let i = take; i < base.cells.length; i++) {
            let cell = cell_1.createUnchangedCellDiffModel(base.cells[i], this.mimetype);
            this.cells.push(cell);
            this.chunkedCells.push([cell]);
        }
    }
}
exports.NotebookDiffModel = NotebookDiffModel;
//# sourceMappingURL=notebook.js.map