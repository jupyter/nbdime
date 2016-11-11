// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
'use strict';


import {
  IDiffEntry, IDiffPatch
} from '../diff/diffentries';

import {
  DiffRangePos
} from '../diff/range';

import {
  MergeDecision
} from '../merge/decisions';

import {
  valueIn, shallowCopy
} from '../common/util';


export
type ChunkSource = {
  decision: MergeDecision;
  action: 'local' | 'remote' | 'either' | 'custom';
};

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
export class Chunk {
  constructor(
      public baseFrom: number,
      public baseTo: number,
      public remoteFrom: number,
      public remoteTo: number,
      source?: ChunkSource) {
    this.sources = source ? [source] : [];
  }

  /**
   * Indicates the source of a chunk in a merge condition.
   *
   * For merged content this can be used to indicate whther the chunk originates
   * from base, local, remote or somewhere else.
   */
  sources: ChunkSource[];

  /**
   * Checks whether the given line number is within the range spanned by editFrom - editTo
   */
  inEdit(line: number) {
    return line >= this.baseFrom && line <= this.baseTo;
  }

  /**
   * Checks whether the given line number is within the range spanned by origFrom - origTo
   */
  inOrig(line: number) {
    return line >= this.remoteFrom && line <= this.remoteTo;
  }

  /**
   *
   */
};

export
class Chunker {
  constructor() {
    this.chunks = [];
    this.editOffset = 0;
  }

  protected _getCurrent() {
    if (this._currentGhost) {
      this._currentGhost = null;
      return null;
    }
    return this.chunks.length > 0 ? this.chunks[this.chunks.length - 1] : null;
  }

  protected _overlapChunk(chunk: Chunk, range: DiffRangePos, isAddition: boolean): boolean {
    if (isAddition) {
      return chunk.inOrig(range.from.line);
    } else {
      return chunk.inEdit(range.from.line);
    }
  }

  addDiff(range: DiffRangePos, isAddition: boolean): void {
    let linediff = range.to.line - range.from.line;
    if (range.endsOnNewline) {
      linediff += 1;
    }
    let firstLineNew = range.from.ch === 0 && linediff > 0;

    let startOffset = range.chunkStartLine ? 0 : 1;
    let endOffset =
      range.chunkStartLine && range.endsOnNewline && firstLineNew ?
      0 : 1;

    let current = this._getCurrent();
    if (current) {
      // Have existing chunk, check for overlap
      if (isAddition) {
        if (this._overlapChunk(current, range, isAddition)) {
          current.remoteTo = Math.max(current.remoteTo,
              range.from.line + endOffset + linediff);
          current.baseTo = Math.max(current.baseTo,
              range.from.line + endOffset + this.editOffset);
          if (range.source && !valueIn(range.source, current.sources)) {
            current.sources.push(range.source);
          }
        } else {
          // No overlap with chunk, start new one
          current = null;
        }
      } else {
        if (this._overlapChunk(current, range, isAddition)) {
          current.remoteTo = Math.max(current.remoteTo,
              range.from.line + endOffset - this.editOffset);
          current.baseTo = Math.max(current.baseTo,
              range.from.line + endOffset + linediff);
          if (range.source && !valueIn(range.source, current.sources)) {
            current.sources.push(range.source);
          }
        } else {
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
        current = new Chunk(
          startBase + startOffset,
          startBase + endOffset,
          startRemote + startOffset,
          startRemote + endOffset + linediff
        );
      } else {
        let startBase = range.from.line;
        let startRemote = startBase - this.editOffset;
        current = new Chunk(
          startBase + startOffset,
          startBase + endOffset + linediff,
          startRemote + startOffset,
          startRemote + endOffset
        );
      }
      if (range.source) {
        current.sources.push(range.source);
      }
      this.chunks.push(current);
    }
    this.editOffset += isAddition ? -linediff : linediff;
  }

  /**
   * Chunk a region where changes will occur if a currently unapplied diff were
   * applied.
   */
  addGhost(range: DiffRangePos, isAddition: boolean, offset: number): void {
    // Do a one-to-one chunk as base
    let linediff = range.to.line - range.from.line;
    if (range.endsOnNewline) {
      linediff += 1;
    }
    let firstLineNew = range.from.ch === 0 && linediff > 0;

    let startOffset = range.chunkStartLine ? 0 : 1;
    let endOffset =
      range.chunkStartLine && range.endsOnNewline && firstLineNew ?
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
        current.remoteTo = Math.max(current.remoteTo,
            startOrig + endOffset);
        current.baseTo = Math.max(current.baseTo,
            startEdit + endOffset);
        if (range.source && !valueIn(range.source, current.sources)) {
          current.sources.push(range.source);
        }
      } else {
        // No overlap with chunk, start new one
        current = null;
      }
    }
    if (!current) {
      let startOrig = startEdit - this.editOffset;
      current = new Chunk(
        startEdit + startOffset,
        startEdit + endOffset,
        startOrig + startOffset,
        startOrig + endOffset
      );
      if (range.source) {
        current.sources.push(range.source);
      }
      this.chunks.push(current);
    }
    this._currentGhost = current;
    // this._doAdd(range, isAddition);
  }

  chunks: Chunk[];
  editOffset: number;

  protected _currentGhost: Chunk | null = null;
}


/**
 * A chunker that only chunks diffs within lines with each other
 *
 * While the default chunker would chunk together a change at the end of one
 * line with a change at the start of the next line, this chunker will keep
 * each line separate. This is useful e.g. for merging.
 */
export
class LineChunker extends Chunker {
  protected _overlapChunk(chunk: Chunk, range: DiffRangePos, isAddition: boolean): boolean {
    let linediff = range.to.line - range.from.line;
    if (range.endsOnNewline) {
      linediff += 1;
    }
    let firstLineNew = range.from.ch === 0 && linediff > 0;
    if (isAddition) {
      return chunk.inOrig(range.from.line + 1);
    } else {
      // Ensure aligned addition/removal on same line
      // still chunk together
      if (chunk.baseFrom === chunk.baseTo && chunk.remoteFrom < chunk.remoteTo) {
        return chunk.inEdit(range.from.line);
      } else {
        return chunk.inEdit(range.from.line + 1);
      }
    }
  }
}


/**
 * Transform an array of lines to normal chunks
 */
export
function lineToNormalChunks(lineChunks: Chunk[]): Chunk[] {
  // We already have line chunks, so simply merge those chunks that overlap
  let current: Chunk | null = null;
  let ret: Chunk[] = [];
  for (let c of lineChunks) {
    if (current === null) {
      current = shallowCopy(c);
    } else {
      if (current.inEdit(c.baseFrom)) {
        // Overlaps, combine
        current.remoteTo = Math.max(current.remoteTo, c.remoteTo);
        current.baseTo = Math.max(current.baseTo, c.baseTo);
        current.sources = current.sources.concat(c.sources);
      } else {
        // No overlap, start new
        ret.push(current);
        current = shallowCopy(c);
      }
    }
  }
  if (current !== null) {
    ret.push(current);
  }
  return ret;
}


/**
 * Label a set of diffs with a source, recursively.
 */
export
function labelSource(diff: IDiffEntry[] | null, source: ChunkSource): IDiffEntry[] | null {
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
