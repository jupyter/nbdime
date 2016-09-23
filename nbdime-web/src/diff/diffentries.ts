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
namespace DiffOp {
  /**
   * An added object entry
   */
  export const ADD = 'add';

  /**
   * A removed object entry
   */
  export const REMOVE = 'remove';

  /**
   * A replaced object entry
   */
  export const REPLACE = 'replace';

  /**
   * A patched entry (object entry or list entry)
   */
  export const PATCH = 'patch';

  /**
   * An added sequence of list entries, or an added substring
   */
  export const SEQINSERT = 'addrange';

  /**
   * A removed sequence of list entries, or a removed substring
   */
  export const SEQDELETE = 'removerange';
}


/**
 * Base class for all diff entries
 */
export interface IDiffEntryBase {
  /**
   * The key of the diff entry: Either the field name in an object, or the
   * index in a list/string.
   */
  key: string | number;

  /**
   * A string identifying the diff operation type, as defined by DiffOp.
   */
  op: string;

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
export interface IDiffAddRange extends IDiffEntryBase {
  key: number;
  /**
   * The sequence of values that were added
   */
  valuelist: string | any[];
}

/**
 * Diff representing an added object entry
 */
export interface IDiffAdd extends IDiffEntryBase {
  /**
   * The value that was added
   */
  value: any;
}


/**
 * Diff representing a removed object entry
 */
export interface IDiffRemove extends IDiffEntryBase {
  // No extra info needed
}


/**
 * Diff representing a replaced object entry
 */
export interface IDiffReplace extends IDiffEntryBase {
  /**
   * The new value
   */
  value: any;
}


/**
 * Diff representing a removed sequence of list entries, or a removed substring
 */
export interface IDiffRemoveRange extends IDiffEntryBase {
  key: number;

  /**
   * The length of the sequence that was deleted
   */
  length: number;
}


/**
 * Diff representing a patched entry (object entry or list entry)
 */
export interface IDiffPatch extends IDiffEntryBase {
  /**
   * The collection of sub-diffs describing the patch of the object
   */
  diff: IDiffEntry[];
}

/**
 * Describes a diff entry of a single JSON value (object, list, string)
 */
export type IDiffEntry = (IDiffAddRange | IDiffRemoveRange | IDiffPatch | IDiffAdd | IDiffRemove | IDiffReplace);


/** Create a replacement diff entry */
export
function opReplace(key: string | number, value: any): IDiffReplace {
  return {op: DiffOp.REPLACE, key: key, value: value};
}

/** Create an addition diff entry */
export
function opAdd(key: string | number, value: any): IDiffAdd {
  return {op: DiffOp.ADD, key: key, value: value};
}

/** Create a removal diff entry */
export
function opRemove(key: string | number): IDiffRemove {
  return {op: DiffOp.REMOVE, key: key};
}

/** Create a removal diff entry */
export
function opAddRange(key: number, valuelist: string | any[]): IDiffAddRange {
  return {op: DiffOp.SEQINSERT, key: key, valuelist: valuelist};
}

/** Create a range removal diff entry */
export
function opRemoveRange(key: number, length: number): IDiffRemoveRange {
  return {op: DiffOp.SEQDELETE, key: key, length: length};
}

/** Create a range removal diff entry */
export
function opPatch(key: string | number, diff: IDiffEntry[]): IDiffPatch {
  return {op: DiffOp.PATCH, key: key, diff: diff};
}


/**
 * Validate that a diff operation is valid to apply on a given base sequence
 */
export
function validateSequenceOp(base: Array<any> | string, entry: IDiffEntry): void {
  let op = entry.op;
  if (typeof entry.key !== 'number') {
      throw 'Invalid patch sequence op: Key is not a number: ' + entry.key;
  }
  let index = entry.key as number;
  if (op === DiffOp.SEQINSERT) {
    if (index < 0 || index > base.length || isNaN(index)) {
      throw 'Invalid add range diff op: Key out of range: ' + index;
    }
  } else if (op === DiffOp.SEQDELETE) {
    if (index < 0 || index >= base.length || isNaN(index)) {
      throw 'Invalid remove range diff op: Key out of range: ' + index;
    }
    let skip = (entry as IDiffRemoveRange).length;
    if (index + skip > base.length || isNaN(index)) {
      throw 'Invalid remove range diff op: Range too long!';
    }
  } else if (op === DiffOp.PATCH) {
    if (index < 0 || index >= base.length || isNaN(index)) {
      throw 'Invalid patch diff op: Key out of range: ' + index;
    }
  } else {
    throw 'Invalid op: ' + op;
  }
}

/**
 * Validate that a diff operation is valid to apply on a given base object
 */
export
function validateObjectOp(base: Object, entry: IDiffEntry, keys: string[]): void {
  let op = entry.op;
  if (typeof entry.key !== 'string') {
      throw 'Invalid patch object op: Key is not a string: ' + entry.key;
  }
  let key = entry.key as string;

  if (op === DiffOp.ADD) {
    if (valueIn(key, keys)) {
      throw 'Invalid add key diff op: Key already present: ' + key;
    }
  } else if (op === DiffOp.REMOVE) {
    if (!valueIn(key, keys)) {
      throw 'Invalid remove key diff op: Missing key: ' + key;
    }
  } else if (op === DiffOp.REPLACE) {
    if (!valueIn(key, keys)) {
      throw 'Invalid replace key diff op: Missing key: ' + key;
    }
  } else if (op === DiffOp.PATCH) {
    if (!valueIn(key, keys)) {
      throw 'Invalid patch key diff op: Missing key: ' + key;
    }
  } else {
    throw 'Invalid op: ' + op;
  }
}
