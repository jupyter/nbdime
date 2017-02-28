// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
'use strict';

import {
  JSONValue, JSONArray, JSONObject
} from '@phosphor/coreutils';

import {
  deepCopy
} from '../common/util';

import {
  IDiffEntry, IDiffArrayEntry, IDiffObjectEntry,
  validateObjectOp, validateSequenceOp
} from '../diff/diffentries';

import {
  patchString
} from './stringified';


/**
 * Patch a base JSON object according to diff. Returns the patched object.
 */
export function patch(base: string, diff: IDiffEntry[] | null): string;
export function patch<T extends JSONArray>(base: T, diff: IDiffEntry[] | null): T;
export function patch<T extends JSONObject>(base: T, diff: IDiffEntry[] | null): T;
export function patch(base: JSONValue, diff: IDiffEntry[] | null): JSONValue;
export function patch(base: JSONValue, diff: IDiffEntry[] | null): JSONValue {
  if (typeof base === 'string') {
    return patchString(base, diff as IDiffArrayEntry[], 0, false).remote;
  } else if (Array.isArray(base)) {
    return patchSequence(base, diff as IDiffArrayEntry[]);
  } else if (typeof base === 'number' || typeof base === 'boolean') {
    throw new TypeError('Cannot patch an atomic type: ' + typeof base);
  } else if (base === null) {
    throw new TypeError('Cannot patch a null base!')
  } else {
    return patchObject(base, diff as IDiffObjectEntry[]);
  }
}


/**
 * Patch an array according to the diff.
 */
function patchSequence(base: JSONArray, diff: IDiffArrayEntry[] | null): JSONArray {
  if (diff === null) {
    return deepCopy(base);
  }
  // The patched sequence to build and return
  let patched: JSONArray = [];
  // Index into obj, the next item to take unless diff says otherwise
  let take = 0;
  let skip = 0;
  for (let e of diff) {
    // Check for valid entry first:
    validateSequenceOp(base, e);
    let index = e.key;

    // Take values from base not mentioned in diff, up to not including
    // index
    for (let value of base.slice(take, index)) {
      patched.push(deepCopy(value));
    }

    if (e.op === 'addrange') {
      // Extend with new values directly
      patched = patched.concat(e.valuelist);
      skip = 0;
    } else if (e.op === 'removerange') {
      // Delete a number of values by skipping
      skip = e.length;
    } else if (e.op === 'patch') {
      patched.push(patch(base[index], e.diff));
      skip = 1;
    }

    // Skip the specified number of elements, but never decrement take.
    // Note that take can pass index in diffs with repeated +/- on the
    // same index, i.e. [op_remove(index), op_add(index, value)]
    take = Math.max(take, index + skip);
  }

  // Take values at end not mentioned in diff
  for (let value of base.slice(take)) {
    patched.push(deepCopy(value));
  }
  return patched;
}


/**
 * Patch an object (dictionary type) according to the diff.
 */
function patchObject(base: JSONObject, diff: IDiffObjectEntry[] | null) : JSONObject {
  let patched: JSONObject = {};
  let keysToCopy = Object.keys(base);

  if (diff) {
    for (let e of diff) {
      // Check for valid entry first:
      validateObjectOp(base, e, keysToCopy);
      let key = e.key;

      if (e.op === 'add') {
        patched[key] = e.value;
      } else if (e.op === 'remove') {
        keysToCopy.splice(keysToCopy.indexOf(key), 1);   // Remove key
      } else if (e.op === 'replace') {
        keysToCopy.splice(keysToCopy.indexOf(key), 1);   // Remove key
        patched[key] = e.value;
      } else if (e.op === 'patch') {
        keysToCopy.splice(keysToCopy.indexOf(key), 1);   // Remove key
        patched[key] = patch(base[key]!, e.diff);
      }
    }
  }

  // Take items not mentioned in diff
  for (let key of keysToCopy) {
    patched[key] = deepCopy(base[key]);
  }
  return patched;
}
