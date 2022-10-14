// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
'use strict';
Object.defineProperty(exports, "__esModule", { value: true });
exports.labelSource = exports.lineToNormalChunks = exports.LineChunker = exports.Chunker = exports.Chunk = void 0;
const util_1 = require("../common/util");
/**
 * A chunk is a range of lines in a string based diff
 * that logically belong together.
 *
 * Chunks can be used for:
 *  - Correlating diff entries in the base and remote, e.g.
 *    for aligning lines in two editors.
 *  - Finding parts of the unchanged text that are not needed
 *    as context (can be hidden)
 *  - Navigating a diff ("Go to next diff")
 */
class Chunk {
    constructor(baseFrom, baseTo, remoteFrom, remoteTo, source) {
        this.baseFrom = baseFrom;
        this.baseTo = baseTo;
        this.remoteFrom = remoteFrom;
        this.remoteTo = remoteTo;
        this.sources = source ? [source] : [];
    }
    /**
     * Checks whether the given line number is within the range spanned by editFrom - editTo
     */
    inEdit(line) {
        return line >= this.baseFrom && line <= this.baseTo;
    }
    /**
     * Checks whether the given line number is within the range spanned by origFrom - origTo
     */
    inOrig(line) {
        return line >= this.remoteFrom && line <= this.remoteTo;
    }
}
exports.Chunk = Chunk;
;
class Chunker {
    constructor() {
        this._currentGhost = null;
        this.chunks = [];
        this.editOffset = 0;
    }
    _getCurrent() {
        if (this._currentGhost) {
            this._currentGhost = null;
            return null;
        }
        return this.chunks.length > 0 ? this.chunks[this.chunks.length - 1] : null;
    }
    _overlapChunk(chunk, range, isAddition) {
        if (isAddition) {
            return chunk.inOrig(range.from.line);
        }
        else {
            return chunk.inEdit(range.from.line);
        }
    }
    addDiff(range, isAddition) {
        let linediff = range.to.line - range.from.line;
        if (range.endsOnNewline) {
            linediff += 1;
        }
        const firstLineNew = range.from.ch === 0 && linediff > 0;
        const startOffset = range.chunkStartLine ? 0 : 1;
        const endOffset = range.chunkStartLine && range.endsOnNewline && firstLineNew ?
            0 : 1;
        let current = this._getCurrent();
        if (current) {
            // Have existing chunk, check for overlap
            if (isAddition) {
                if (this._overlapChunk(current, range, isAddition)) {
                    current.remoteTo = Math.max(current.remoteTo, range.from.line + endOffset + linediff);
                    current.baseTo = Math.max(current.baseTo, range.from.line + endOffset + this.editOffset);
                    if (range.source && !util_1.valueIn(range.source, current.sources)) {
                        current.sources.push(range.source);
                    }
                }
                else {
                    // No overlap with chunk, start new one
                    current = null;
                }
            }
            else {
                if (this._overlapChunk(current, range, isAddition)) {
                    current.remoteTo = Math.max(current.remoteTo, range.from.line + endOffset - this.editOffset);
                    current.baseTo = Math.max(current.baseTo, range.from.line + endOffset + linediff);
                    if (range.source && !util_1.valueIn(range.source, current.sources)) {
                        current.sources.push(range.source);
                    }
                }
                else {
                    // No overlap with chunk, start new one
                    current = null;
                }
            }
        }
        if (!current) {
            // No current chunk, start a new one
            if (isAddition) {
                let startRemote = range.from.line;
                let startBase = startRemote + this.editOffset;
                current = new Chunk(startBase + startOffset, startBase + endOffset, startRemote + startOffset, startRemote + endOffset + linediff);
            }
            else {
                let startBase = range.from.line;
                let startRemote = startBase - this.editOffset;
                current = new Chunk(startBase + startOffset, startBase + endOffset + linediff, startRemote + startOffset, startRemote + endOffset);
            }
            if (range.source) {
                current.sources.push(range.source);
            }
            this.chunks.push(current);
        }
        current.sources = current.sources.filter(util_1.unique);
        this.editOffset += isAddition ? -linediff : linediff;
    }
    /**
     * Chunk a region where changes will occur if a currently unapplied diff were
     * applied.
     */
    addGhost(range, isAddition, offset) {
        // Do a one-to-one chunk as base
        let linediff = range.to.line - range.from.line;
        if (range.endsOnNewline) {
            linediff += 1;
        }
        let firstLineNew = range.from.ch === 0 && linediff > 0;
        let startOffset = range.chunkStartLine ? 0 : 1;
        let endOffset = range.chunkStartLine && range.endsOnNewline && firstLineNew ?
            0 : 1;
        if (!isAddition) {
            endOffset += linediff;
        }
        let current = this._currentGhost;
        // Subtract offset from other editor
        let startEdit = range.from.line + (isAddition ? offset : 0);
        if (current) {
            // Have existing chunk, check for overlap
            let startOrig = startEdit - this.editOffset;
            if (current.baseTo > startEdit) {
                current.remoteTo = Math.max(current.remoteTo, startOrig + endOffset);
                current.baseTo = Math.max(current.baseTo, startEdit + endOffset);
                if (range.source && !util_1.valueIn(range.source, current.sources)) {
                    current.sources.push(range.source);
                }
            }
            else {
                // No overlap with chunk, start new one
                current = null;
            }
        }
        if (!current) {
            let startOrig = startEdit - this.editOffset;
            current = new Chunk(startEdit + startOffset, startEdit + endOffset, startOrig + startOffset, startOrig + endOffset);
            if (range.source) {
                current.sources.push(range.source);
            }
            this.chunks.push(current);
        }
        this._currentGhost = current;
        current.sources = current.sources.filter(util_1.unique);
        // this._doAdd(range, isAddition);
    }
}
exports.Chunker = Chunker;
/**
 * A chunker that only chunks diffs within lines with each other
 *
 * While the default chunker would chunk together a change at the end of one
 * line with a change at the start of the next line, this chunker will keep
 * each line separate. This is useful e.g. for merging.
 */
class LineChunker extends Chunker {
    _overlapChunk(chunk, range, isAddition) {
        let fromLine = range.from.line;
        if (chunk.baseFrom !== chunk.baseTo || chunk.remoteFrom >= chunk.remoteTo) {
            // Ensure aligned addition/removal on same line
            // still chunk together
            fromLine += 1;
        }
        if (isAddition) {
            return chunk.inOrig(fromLine);
        }
        else {
            return chunk.inEdit(fromLine);
        }
    }
}
exports.LineChunker = LineChunker;
/**
 * Transform an array of lines to normal chunks
 */
function lineToNormalChunks(lineChunks) {
    // We already have line chunks, so simply merge those chunks that overlap
    let current = null;
    let ret = [];
    for (let c of lineChunks) {
        if (current === null) {
            current = util_1.shallowCopy(c);
        }
        else {
            if (current.inEdit(c.baseFrom)) {
                // Overlaps, combine
                current.remoteTo = Math.max(current.remoteTo, c.remoteTo);
                current.baseTo = Math.max(current.baseTo, c.baseTo);
                current.sources = current.sources.concat(c.sources);
            }
            else {
                // No overlap, start new
                ret.push(current);
                current = util_1.shallowCopy(c);
            }
        }
        current.sources = current.sources.filter(util_1.unique);
    }
    if (current !== null) {
        ret.push(current);
    }
    return ret;
}
exports.lineToNormalChunks = lineToNormalChunks;
/**
 * Label a set of diffs with a source, recursively.
 */
function labelSource(diff, source) {
    if (diff) {
        for (let d of diff) {
            d.source = source;
            if (d.op === 'patch') {
                labelSource(d.diff, source);
            }
        }
    }
    return diff;
}
exports.labelSource = labelSource;
//# sourceMappingURL=diffchunking.js.map