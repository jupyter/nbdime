// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
'use strict';

import {
  valueIn, sortByKey, shallowCopy, accumulateLengths
} from '../common/util';

import {
  IDiffEntry, IDiffPatch, IDiffAddRange, IDiffRemoveRange,
  IDiffAdd, opAddRange, opRemoveRange, validateSequenceOp
} from './diffentries';

/**
 * The indentation to use for JSON stringify.
 */
export const JSON_INDENT = '  ';


/**
 * Search the list of diffs for an entry with the given key.
 *
 * Returns the first found entry, or null if not entry was found.
 */
export
function getDiffKey(diff: IDiffEntry[], key: string | number) : IDiffEntry[] {
  for (let i=0; i < diff.length; ++i) {
    if (diff[i].key === key) {
      return (diff[i] as IDiffPatch).diff;
    }
  }
  return null;
}


function validateStringDiff(base: string[], entry: IDiffEntry, lineToChar: number[]): void {
  // First valdiate line ops:
  validateSequenceOp(base, entry);

  if (entry.op === 'patch') {
    let line = base[entry.key as number];
    let diff = (entry as IDiffPatch).diff;
    for (let d of diff) {
      validateSequenceOp(line, d);
    }
  }
}

let addops = ['add', 'addrange'];

/**
 * Check whether existing collection of diff ops shares a key with the new
 * diffop, and if they  also have the same op type.
 */
function overlaps(existing: IDiffEntry[], newv: IDiffEntry): boolean {
  if (existing.length < 1) {
    return false;
  }
  for (let e of existing) {
    if (e.op === newv.op) {
      if (e.key === newv.key) {
        // Found a match
        return true;
      } else if (e.op === 'removerange') {
        let r = e as IDiffRemoveRange;
        let first = r.key < newv.key ? r : newv as IDiffRemoveRange;
        let last = r.key > newv.key ? r : newv as IDiffRemoveRange;
        if (first.key + first.length >= last.key) {
          // Overlapping deletes
          // Above check is open ended to allow for sanity check here:
          if (first.key + first.length !== last.key) {
            throw 'Overlapping delete diff ops: ' +
              'Two operation remove same characters!';
          }
          return true;
        }
      }
    } else if (valueIn(e.op, addops) && valueIn(newv.op, addops) &&
              e.key === newv.key) {
      // Addrange and single add can both point to same key
      return true;
    }
  }
  return false;
}


/**
 * Combines two ops into a new one that does the same
 */
function combineOps(a: IDiffEntry, b: IDiffEntry): IDiffEntry {
  if (valueIn(b.op, addops)) {
    let aTyped: IDiffAddRange = null;
    if (a.op === 'add') {
      aTyped = opAddRange(a.key as number, [(a as IDiffAdd).value]);
    } else {
      aTyped = opAddRange(a.key as number, (a as IDiffAddRange).valuelist);
    }
    aTyped.source = a.source;
    if (b.source !== a.source) {
      throw 'Cannot combine diff ops with different sources in one string line';
    }
    if (b.op === 'addrange') {
      let bTyped = b as IDiffAddRange;
      // valuelist can also be string, but string also has concat:
      (aTyped.valuelist as any[]).concat(bTyped.valuelist as any[]);
    } else {
      let bTyped = b as IDiffAdd;
      if (typeof aTyped.valuelist === 'string') {
        aTyped.valuelist += bTyped.value;
      } else {
        (aTyped.valuelist as any[]).push(bTyped.value);
      }
    }
    return aTyped;
  } else if (b.op === 'removerange') {
    if (a.op !== 'removerange') {
      throw 'Cannot combine operations: ' + a + ', ' + b;
    }
    let aTyped = a as IDiffRemoveRange;
    let bTyped = b as IDiffRemoveRange;
    return opRemoveRange(aTyped.key, aTyped.length + bTyped.length);
  }
}


/**
 * Translates a diff of strings split by str.splitlines() to a diff of the
 * joined multiline string
 */
export
function flattenStringDiff(val: string[] | string, diff: IDiffEntry[]): IDiffEntry[] {

  if (typeof val === 'string') {
    // Split lines (retaining newlines):
    val = (val as string).match(/^.*([\n\r]|$)/gm);
  }
  let a = val as string[];
  let lineToChar = [0].concat(accumulateLengths(a));
  let flattened: IDiffEntry[] = [];
  for (let e of diff) {
    // Frist validate op:
    validateStringDiff(a, e, lineToChar);
    let op = e.op;
    let lineOffset = lineToChar[e.key];
    if (op === 'patch') {
      for (let p of (e as IDiffPatch).diff) {
        let d = shallowCopy(p);
        d.key += lineOffset;
        if (overlaps(flattened, d)) {
          flattened[-1] = combineOps(flattened[-1], d);
        } else {
          flattened.push(d);
        }
      }
    } else {
      // Other ops simply have keys which refer to lines
      let d: IDiffEntry = null;
      if (op === 'addrange') {
        let et = e as IDiffAddRange;
        d = opAddRange(lineOffset,
                       (et.valuelist as any[]).join(''));
      } else if (op === 'removerange') {
        let et = e as IDiffRemoveRange;
        let idx = et.key + et.length;
        d = opRemoveRange(lineOffset,
                          lineToChar[idx] - lineOffset);
      }
      d.source = e.source;

      if (overlaps(flattened, d)) {
        flattened[-1] = combineOps(flattened[-1], d);
      } else {
        flattened.push(d);
      }
    }
  }
  // Finally, sort on key (leaving equal items in original order)
  // This is done since the original diffs are sorted deeper first!
  return sortByKey(flattened, 'key');
}
