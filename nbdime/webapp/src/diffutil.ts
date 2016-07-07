// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
'use strict';

import * as CodeMirror from 'codemirror';

import { 
  valueIn
} from './util'; 

/**
 * The indentation to use for JSON stringify.
 */
export const JSON_INDENT = '  ';


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
}


/**
 * Diff representing an added sequence of list entries, or an added substring
 */
export interface IDiffAddRange extends IDiffEntryBase {
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

/**
 * Search the list of diffs for an entry with the given key.
 * 
 * Returns the first found entry, or null if not entry was found.
 */
export function getDiffKey(diff: IDiffEntry[], key:string) : IDiffEntry[] {
  for (var i=0; i<diff.length; ++i) {
    if (diff[i].key == key) {
      return (diff[i] as IDiffPatch).diff;
    }
  }
  return null;
}
