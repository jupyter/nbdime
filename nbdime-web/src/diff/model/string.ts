// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
'use strict';

import {
  nbformat
} from '@jupyterlab/coreutils';

import {
  JSONObject, JSONArray, JSONValue
} from '@phosphor/coreutils';

import {
  IDiffEntry
} from '../diffentries';

import {
  DiffRangeRaw, DiffRangePos, raw2Pos
} from '../range';

import {
  Chunk, LineChunker
} from '../../chunking';

import {
  patchStringified, stringifyAndBlankNull
} from '../../patch';

import {
  IDiffModel
} from './common';


/**
 * Interface for a string diff model.
 *
 * String diff models are used for any content where the final
 * diff should be presented as a difference between strings
 * (as compared to e.g. images). As such, it is NOT restricted
 * to cases where original content is in a string format.
 */
export
interface IStringDiffModel extends IDiffModel {
  /**
   * Base value
   */
  base: string | null;

  /**
   * Remote value
   */
  remote: string | null;

  /**
   * Mimetype of the data the string represents.
   *
   * Can be used for things such as syntax highlighting.
   */
  mimetype: string;

  /**
   * Location of additions, as positions in the remote value.
   *
   * Locations should be sorted on the ranges' `from` position
   */
  additions: DiffRangePos[];

  /**
   * Location of deletions, as positions in the base value.
   *
   * Locations should be sorted on the ranges' `from` position
   */
  deletions: DiffRangePos[];

  /**
   * A function that will separate the diff into chunks.
   */
  getLineChunks(): Chunk[];

  /**
   * Create an iterator for iterating over the diffs in order
   */
  iterateDiffs(): StringDiffModel.DiffIter;
}


/**
 * Standard implementation of the IStringDiffModel interface.
 */
export
class StringDiffModel implements IStringDiffModel {

  /**
   * StringDiffModel constructor.
   *
   * Will translate additions and deletions from absolute
   * coordinates, into {line, ch} based coordinates.
   * Both should be sorted on the `from` position before passing.
   *
   * Collapsible and collapsed both defaults to false.
   */
  constructor(
        public base: string | null,
        public remote: string | null,
        additions: DiffRangeRaw[],
        deletions: DiffRangeRaw[],
        collapsible?: boolean,
        header?: string,
        collapsed?: boolean) {
    if (base === null) {
      console.assert(deletions.length === 0);
      this.deletions = [];
    } else {
      this.deletions = raw2Pos(deletions, base);
    }
    if (remote === null) {
      console.assert(additions.length === 0);
      this.additions = [];
    } else {
      this.additions = raw2Pos(additions, remote);
    }

    this.collapsible = collapsible === true;
    if (this.collapsible) {
      this.collapsibleHeader = header ? header : '';
      this.startCollapsed = collapsed === true;
    }
  }

  iterateDiffs(): StringDiffModel.DiffIter  {
    return new StringDiffModel.DiffIter(this);
  }

  /**
   * Chunk additions/deletions into line-based chunks
   */
  getLineChunks(): Chunk[] {
    let chunker = new LineChunker();
    let i = this.iterateDiffs();
    for (let v = i.next(); v !== undefined; v = i.next()) {
      chunker.addDiff(v.range, v.isAddition);
    }
    return chunker.chunks;
  }

  get unchanged(): boolean {
    return this.base === this.remote;
  }

  get added(): boolean {
    return this.base === null;
  }

  get deleted(): boolean {
    return this.remote === null;
  }

  collapsible: boolean;
  collapsibleHeader: string;
  startCollapsed: boolean;

  mimetype: string;

  additions: DiffRangePos[];
  deletions: DiffRangePos[];
}


export
namespace StringDiffModel {
  export
  type DiffIterValue = {range: DiffRangePos, isAddition: boolean} | undefined;

  export
  interface IIterator<T> {
    next(): T | undefined;
  }

  export
  class DiffIter implements IIterator<DiffIterValue> {
    constructor(model: IStringDiffModel) {
      this.model = model;
    }

    next(): DiffIterValue | undefined {
      // Figure out which element to take next
      let isAddition: boolean | null = null;
      let range: DiffRangePos | null = null;
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
            } else {
              this.hintTakeDeletion = true;
              isAddition = true;
            }
          } else if (ra.from.line < rd.from.line - this.editOffset ||
                (ra.from.line === rd.from.line - this.editOffset &&
                  ra.from.ch < rd.from.ch)) {
            // TODO: Character editOffset should also be used
            isAddition = true;
          } else {
            isAddition = false;
          }
        } else {
          // No more deletions
          isAddition = true;
        }
      } else if (this.id < deletions.length) {
        // No more additions
        isAddition = false;
      } else {
        // Out of ranges!
        this.done = true;
        return undefined;
      }

      if (isAddition) {
        range = additions[this.ia++];
      } else {
        range = deletions[this.id++];
      }
      let linediff = range.to.line - range.from.line;
      if (range.endsOnNewline) {
        linediff += 1;
      }
      this.editOffset += isAddition ? -linediff : linediff;
      return {range: range, isAddition: isAddition};
    }

    editOffset = 0;
    done = false;

    protected model: IStringDiffModel;
    protected ia = 0;
    protected id = 0;
    protected hintTakeDeletion = false;
  }

  export
  class SyncedDiffIter implements IIterator<DiffIterValue> {
    static cmp(a: DiffIterValue, b: DiffIterValue,
               offsetA: number, offsetB: number) {
      if (a === undefined && b === undefined) {
        return 0;
      } else if (a === undefined) {
        return 1;
      } else if (b === undefined) {
        return -1;
      }
      let lineA = a.range.from.line  + (a.isAddition ? offsetA : 0);
      let lineB = b.range.from.line  + (b.isAddition ? offsetB : 0);
      if (lineA < lineB || a.range.from.ch < b.range.from.ch) {
        return -1;
      } else if (lineA > lineB || a.range.from.ch > b.range.from.ch) {
        return 1;
      } else {
        return 0;
      }
    }

    constructor(models: (IStringDiffModel | null)[]) {
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

    next(): DiffIterValue {
      // Compare in base index to see which diff is next
      let i = 0;
      for (let j = 1; j < this.values.length; ++j) {
        if (0 > SyncedDiffIter.cmp(this.values[j], this.values[i],
                                   this.iterators[j].editOffset,
                                   this.iterators[i].editOffset)) {
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

    currentModel(): IStringDiffModel {
      return this.models[this.i];
    }

    currentOffset = 0;

    protected i: number;

    protected models: IStringDiffModel[];
    protected iterators: DiffIter[];
    protected values: DiffIterValue[];
    protected offsets: number[];
  }
}


/**
 * Creates a StringDiffModel based on a patch operation.
 *
 * If base is not a string, it is assumed to be a JSON object/array,
 * and it will be stringified according to JSON stringification
 * rules.
 */
export
function createPatchStringDiffModel(base: string | JSONObject | JSONArray, diff: IDiffEntry[]) : StringDiffModel {
  console.assert(!!diff, 'Patch model needs diff.');
  let baseStr = stringifyAndBlankNull(base);
  let out = patchStringified(base, diff);
  return new StringDiffModel(baseStr, out.remote, out.additions, out.deletions);
}


/**
 * Factory for creating cell diff models for added, removed or unchanged content.
 *
 * If base is null, it will be treated as added, if remote is null it will be
 * treated as removed. Otherwise base and remote should be equal, represeting
 * unchanged content.
 */
export
function createDirectStringDiffModel(base: JSONValue | null, remote: JSONValue | null): StringDiffModel {
  let baseStr: string | null = stringifyAndBlankNull(base);
  let remoteStr: string | null = stringifyAndBlankNull(remote);
  let additions: DiffRangeRaw[] = [];
  let deletions: DiffRangeRaw[] = [];

  if (base === null && remote === null) {
    throw new Error('Invalid arguments to createDirectStringDiffModel(). ' +
      'Both base and remote cannot be equal!');
  } else if (base === null) {
    // Added cell
    baseStr = null;
    additions.push(new DiffRangeRaw(0, remoteStr.length, undefined));
  } else if (remote === null) {
    // Deleted cell
    remoteStr = null;
    deletions.push(new DiffRangeRaw(0, baseStr.length, undefined));
  } else if (remoteStr !== baseStr) {
    throw new Error('Invalid arguments to createDirectStringDiffModel(). ' +
      'Either base or remote should be null, or they should be equal!');
  }
  return new StringDiffModel(baseStr, remoteStr, additions, deletions);
}


/**
 * Assign MIME type to an IStringDiffModel based on the cell type.
 *
 * The parameter nbMimetype is the MIME type set for the entire notebook, and is
 * used as the MIME type for code cells.
 */
export
function setMimetypeFromCellType(model: IStringDiffModel, cell: nbformat.ICell,
                                 nbMimetype: string) {
  if (cell.cell_type === 'code') {
    model.mimetype = nbMimetype;
  } else if (cell.cell_type === 'markdown') {
    model.mimetype = 'text/markdown';
  } else if (nbformat.isRaw(cell)) {
    model.mimetype = cell.metadata.format || 'text/plain';
  }
}
