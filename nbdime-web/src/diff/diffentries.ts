// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
'use strict';

import {
  valueIn
} from '../common/util';

import {
  ChunkSource
} from '../chunking';

/**
 * The different diff operations available
 */
export
type DiffOp = 'add' | 'remove' | 'replace' | 'patch' |
  'addrange' | 'removerange';


/**
 * Base interface for all diff entries
 */
export
interface IDiffEntryBase {
  /**
   * The key of the diff entry: Either the field name in an object, or the
   * index in a list/string.
   */
  key: string | number;

  /**
   * A string identifying the diff operation type, as defined by DiffOp.
   */
  op: DiffOp;

  /**
   * Optional: Source of diff, for use when merging.
   *
   * This should not need to be set manually.
   */
  source?: ChunkSource;
}


/**
 * Diff representing an added sequence of list entries, or an added substring
 */
export
interface IDiffAddRange extends IDiffEntryBase {
  op: 'addrange';
  key: number;
  /**
   * The sequence of values that were added
   */
  valuelist: string | any[];
}

/**
 * Diff representing an added object entry
 */
export
interface IDiffAdd extends IDiffEntryBase {
  op: 'add';
  key: string;
  /**
   * The value that was added
   */
  value: any;
}


/**
 * Diff representing a removed object entry
 */
export
interface IDiffRemove extends IDiffEntryBase {
  op: 'remove';
  key: string;
}


/**
 * Diff representing a replaced object entry
 */
export
interface IDiffReplace extends IDiffEntryBase {
  op: 'replace';
  key: string;
  /**
   * The new value
   */
  value: any;
}


/**
 * Diff representing a removed sequence of list entries, or a removed substring
 */
export
interface IDiffRemoveRange extends IDiffEntryBase {
  op: 'removerange';
  key: number;

  /**
   * The length of the sequence that was deleted
   */
  length: number;
}


/**
 * Diff representing a patched entry (object entry or list entry)
 */
export
interface IDiffPatch extends IDiffEntryBase {
  op: 'patch';
  /**
   * The collection of sub-diffs describing the patch of the object
   */
  diff: IDiffEntry[] | null;
}
export
interface IDiffPatchArray extends IDiffPatch {
  key: number;
}
export
interface IDiffPatchObject extends IDiffPatch {
  key: string;
}

/**
 * Describes a diff entry of a single JSON value (object, list, string)
 */
export
type IDiffEntry = IDiffAddRange | IDiffRemoveRange | IDiffPatch | IDiffAdd | IDiffRemove | IDiffReplace;

export
type IDiffArrayEntry = IDiffAddRange | IDiffRemoveRange | IDiffPatchArray;

export
type IDiffObjectEntry = IDiffPatchObject | IDiffAdd | IDiffRemove | IDiffReplace;

export
type IDiffImmutableArrayEntry = IDiffAddRange | IDiffRemoveRange;

export
type IDiffImmutableObjectEntry = IDiffAdd | IDiffRemove | IDiffReplace;


export
type DiffCollection = (IDiffEntry[] | null)[];


/** Create a replacement diff entry */
export
function opReplace(key: string, value: any): IDiffReplace {
  return {op: 'replace', key: key, value: value};
}

/** Create an addition diff entry */
export
function opAdd(key: string, value: any): IDiffAdd {
  return {op: 'add', key: key, value: value};
}

/** Create a removal diff entry */
export
function opRemove(key: string): IDiffRemove {
  return {op: 'remove', key: key};
}

/** Create a removal diff entry */
export
function opAddRange(key: number, valuelist: string | any[]): IDiffAddRange {
  return {op: 'addrange', key: key, valuelist: valuelist};
}

/** Create a range removal diff entry */
export
function opRemoveRange(key: number, length: number): IDiffRemoveRange {
  return {op: 'removerange', key: key, length: length};
}

/** Create a range removal diff entry */
export
function opPatch(key: string | number, diff: IDiffEntry[] | null): IDiffPatch {
  return {op: 'patch', key: key, diff: diff};
}


/**
 * Validate that a diff operation is valid to apply on a given base sequence
 */
export
function validateSequenceOp(base: ReadonlyArray<any> | string, entry: IDiffEntry): void {
  if (typeof entry.key !== 'number') {
      throw new TypeError('Invalid patch sequence op: Key is not a number: ' + entry.key);
  }
  let index = entry.key;
  if (entry.op === 'addrange') {
    if (index < 0 || index > base.length || isNaN(index)) {
      throw new RangeError('Invalid add range diff op: Key out of range: ' + index);
    }
  } else if (entry.op === 'removerange') {
    if (index < 0 || index >= base.length || isNaN(index)) {
      throw new RangeError('Invalid remove range diff op: Key out of range: ' + index);
    }
    let skip = entry.length;
    if (index + skip > base.length || isNaN(index)) {
      throw new RangeError('Invalid remove range diff op: Range too long!');
    }
  } else if (entry.op === 'patch') {
    if (index < 0 || index >= base.length || isNaN(index)) {
      throw new RangeError('Invalid patch diff op: Key out of range: ' + index);
    }
  } else {
    throw new Error('Invalid op: ' + entry.op);
  }
}

/**
 * Validate that a diff operation is valid to apply on a given base object
 */
export
function validateObjectOp(base: any, entry: IDiffEntry, keys: string[]): void {
  let op = entry.op;
  if (typeof entry.key !== 'string') {
      throw new TypeError('Invalid patch object op: Key is not a string: ' + entry.key);
  }
  let key = entry.key;

  if (op === 'add') {
    if (valueIn(key, keys)) {
      throw new Error('Invalid add key diff op: Key already present: ' + key);
    }
  } else if (op === 'remove') {
    if (!valueIn(key, keys)) {
      throw new Error('Invalid remove key diff op: Missing key: ' + key);
    }
  } else if (op === 'replace') {
    if (!valueIn(key, keys)) {
      throw new Error('Invalid replace key diff op: Missing key: ' + key);
    }
  } else if (op === 'patch') {
    if (!valueIn(key, keys)) {
      throw new Error('Invalid patch key diff op: Missing key: ' + key);
    }
  } else {
    throw new Error('Invalid op: ' + op);
  }
}
