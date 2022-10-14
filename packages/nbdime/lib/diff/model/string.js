// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
'use strict';
Object.defineProperty(exports, "__esModule", { value: true });
exports.setMimetypeFromCellType = exports.createDirectStringDiffModel = exports.createPatchStringDiffModel = exports.StringDiffModel = void 0;
const nbformat = require("@jupyterlab/nbformat");
const coreutils_1 = require("@lumino/coreutils");
const range_1 = require("../range");
const chunking_1 = require("../../chunking");
const patch_1 = require("../../patch");
/**
 * Standard implementation of the IStringDiffModel interface.
 */
class StringDiffModel {
    /**
     * StringDiffModel constructor.
     *
     * Will translate additions and deletions from absolute
     * coordinates, into {line, ch} based coordinates.
     * Both should be sorted on the `from` position before passing.
     *
     * Collapsible and collapsed both defaults to false.
     */
    constructor(base, remote, additions, deletions, collapsible, header, collapsed) {
        this.base = base;
        this.remote = remote;
        if (base === null) {
            console.assert(deletions.length === 0);
            this.deletions = [];
        }
        else {
            this.deletions = range_1.raw2Pos(deletions, base);
        }
        if (remote === null) {
            console.assert(additions.length === 0);
            this.additions = [];
        }
        else {
            this.additions = range_1.raw2Pos(additions, remote);
        }
        this.collapsible = collapsible === true;
        if (this.collapsible) {
            this.collapsibleHeader = header ? header : '';
            this.startCollapsed = collapsed === true;
        }
    }
    iterateDiffs() {
        return new StringDiffModel.DiffIter(this);
    }
    /**
     * Chunk additions/deletions into line-based chunks
     */
    getLineChunks() {
        let chunker = new chunking_1.LineChunker();
        let i = this.iterateDiffs();
        for (let v = i.next(); v !== undefined; v = i.next()) {
            chunker.addDiff(v.range, v.isAddition);
        }
        return chunker.chunks;
    }
    get unchanged() {
        return this.base === this.remote;
    }
    get added() {
        return this.base === null;
    }
    get deleted() {
        return this.remote === null;
    }
}
exports.StringDiffModel = StringDiffModel;
(function (StringDiffModel) {
    class DiffIter {
        constructor(model) {
            this.editOffset = 0;
            this.done = false;
            this.ia = 0;
            this.id = 0;
            this.hintTakeDeletion = false;
            this.model = model;
        }
        next() {
            // Figure out which element to take next
            let isAddition = null;
            let range = null;
            let additions = this.model.additions;
            let deletions = this.model.deletions;
            let hintTakeDeletion = this.hintTakeDeletion;
            this.hintTakeDeletion = false;
            if (this.ia < this.model.additions.length) {
                if (this.id < deletions.length) {
                    let ra = additions[this.ia];
                    let rd = deletions[this.id];
                    if (ra.from.line === rd.from.line - this.editOffset &&
                        ra.from.ch === rd.from.ch) {
                        // An addition and deletion start at seemingly same location
                        // Take addition, and flag to ensure deletion gets taken next
                        if (hintTakeDeletion) {
                            isAddition = false;
                        }
                        else {
                            this.hintTakeDeletion = true;
                            isAddition = true;
                        }
                    }
                    else if (ra.from.line < rd.from.line - this.editOffset ||
                        (ra.from.line === rd.from.line - this.editOffset &&
                            ra.from.ch < rd.from.ch)) {
                        // TODO: Character editOffset should also be used
                        isAddition = true;
                    }
                    else {
                        isAddition = false;
                    }
                }
                else {
                    // No more deletions
                    isAddition = true;
                }
            }
            else if (this.id < deletions.length) {
                // No more additions
                isAddition = false;
            }
            else {
                // Out of ranges!
                this.done = true;
                return undefined;
            }
            if (isAddition) {
                range = additions[this.ia++];
            }
            else {
                range = deletions[this.id++];
            }
            let linediff = range.to.line - range.from.line;
            if (range.endsOnNewline) {
                linediff += 1;
            }
            this.editOffset += isAddition ? -linediff : linediff;
            return { range: range, isAddition: isAddition };
        }
    }
    StringDiffModel.DiffIter = DiffIter;
    class SyncedDiffIter {
        constructor(models) {
            this.currentOffset = 0;
            this.models = [];
            this.iterators = [];
            this.values = [];
            this.offsets = [];
            // Set up iterator and dummy chunkers for other models
            for (let m of models) {
                if (m === null) {
                    continue;
                }
                this.models.push(m);
                let it = m.iterateDiffs();
                this.iterators.push(it);
                this.offsets.push(0);
                this.values.push(it.next());
            }
        }
        static cmp(a, b, offsetA, offsetB) {
            if (a === undefined && b === undefined) {
                return 0;
            }
            else if (a === undefined) {
                return 1;
            }
            else if (b === undefined) {
                return -1;
            }
            let lineA = a.range.from.line + (a.isAddition ? offsetA : 0);
            let lineB = b.range.from.line + (b.isAddition ? offsetB : 0);
            if (lineA < lineB || a.range.from.ch < b.range.from.ch) {
                return -1;
            }
            else if (lineA > lineB || a.range.from.ch > b.range.from.ch) {
                return 1;
            }
            else {
                return 0;
            }
        }
        next() {
            // Compare in base index to see which diff is next
            let i = 0;
            for (let j = 1; j < this.values.length; ++j) {
                if (0 > SyncedDiffIter.cmp(this.values[j], this.values[i], this.iterators[j].editOffset, this.iterators[i].editOffset)) {
                    i = j;
                }
            }
            this.i = i;
            let ret = this.values[i];
            // Store the edit offset before taking next value
            this.currentOffset = this.offsets[i];
            this.offsets[i] = this.iterators[i].editOffset;
            // Check if complete
            if (ret !== undefined) {
                this.values[i] = this.iterators[i].next();
            }
            return ret;
        }
        currentModel() {
            return this.models[this.i];
        }
    }
    StringDiffModel.SyncedDiffIter = SyncedDiffIter;
})(StringDiffModel = exports.StringDiffModel || (exports.StringDiffModel = {}));
/**
 * Creates a StringDiffModel based on a patch operation.
 *
 * If base is not a string, it is assumed to be a JSON object/array,
 * and it will be stringified according to JSON stringification
 * rules.
 */
function createPatchStringDiffModel(base, diff) {
    console.assert(!!diff, 'Patch model needs diff.');
    const baseCopy = coreutils_1.JSONExt.deepCopy(base);
    let baseStr = patch_1.stringifyAndBlankNull(baseCopy);
    let out = patch_1.patchStringified(baseCopy, diff);
    return new StringDiffModel(baseStr, out.remote, out.additions, out.deletions);
}
exports.createPatchStringDiffModel = createPatchStringDiffModel;
/**
 * Factory for creating cell diff models for added, removed or unchanged content.
 *
 * If base is null, it will be treated as added, if remote is null it will be
 * treated as removed. Otherwise base and remote should be equal, represeting
 * unchanged content.
 */
function createDirectStringDiffModel(base, remote) {
    let baseStr = patch_1.stringifyAndBlankNull(base);
    let remoteStr = patch_1.stringifyAndBlankNull(remote);
    let additions = [];
    let deletions = [];
    if (base === null && remote === null) {
        throw new Error('Invalid arguments to createDirectStringDiffModel(). ' +
            'Both base and remote cannot be equal!');
    }
    else if (base === null) {
        // Added cell
        baseStr = null;
        additions.push(new range_1.DiffRangeRaw(0, remoteStr.length, undefined));
    }
    else if (remote === null) {
        // Deleted cell
        remoteStr = null;
        deletions.push(new range_1.DiffRangeRaw(0, baseStr.length, undefined));
    }
    else if (remoteStr !== baseStr) {
        throw new Error('Invalid arguments to createDirectStringDiffModel(). ' +
            'Either base or remote should be null, or they should be equal!');
    }
    return new StringDiffModel(baseStr, remoteStr, additions, deletions);
}
exports.createDirectStringDiffModel = createDirectStringDiffModel;
/**
 * Assign MIME type to an IStringDiffModel based on the cell type.
 *
 * The parameter nbMimetype is the MIME type set for the entire notebook, and is
 * used as the MIME type for code cells.
 */
function setMimetypeFromCellType(model, cell, nbMimetype) {
    if (cell.cell_type === 'code') {
        model.mimetype = nbMimetype;
    }
    else if (cell.cell_type === 'markdown') {
        model.mimetype = 'text/markdown';
    }
    else if (nbformat.isRaw(cell)) {
        model.mimetype = cell.metadata.format || 'text/plain';
    }
}
exports.setMimetypeFromCellType = setMimetypeFromCellType;
//# sourceMappingURL=string.js.map