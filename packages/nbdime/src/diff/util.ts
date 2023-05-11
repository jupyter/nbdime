// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
'use strict';

import {
  sortByKey,
  shallowCopy,
  accumulateLengths,
  splitLines,
} from '../common/util';

import {
  IDiffEntry,
  IDiffArrayEntry,
  IDiffPatch,
  opAddRange,
  opRemoveRange,
  validateSequenceOp,
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
export function getSubDiffByKey(
  diff: IDiffEntry[] | null,
  key: string | number,
): IDiffEntry[] | null {
  if (!diff) {
    return null;
  }
  for (let i = 0; i < diff.length; ++i) {
    if (diff[i].key === key) {
      return (diff[i] as IDiffPatch).diff || null;
    }
  }
  return null;
}

/**
 * Search the list of diffs for an entry with the given key.
 *
 * Returns the first found entry, or null if not entry was found.
 */
export function getDiffEntryByKey(
  diff: IDiffEntry[] | null,
  key: string | number,
): IDiffEntry | null {
  if (!diff) {
    return null;
  }
  for (let i = 0; i < diff.length; ++i) {
    if (diff[i].key === key) {
      return diff[i];
    }
  }
  return null;
}

function validateStringDiff(
  base: string[],
  entry: IDiffArrayEntry,
  lineToChar: number[],
): void {
  // First valdiate line ops:
  validateSequenceOp(base, entry);

  if (entry.op === 'patch') {
    let line = base[entry.key];
    let diff = entry.diff;
    if (diff !== null) {
      for (let d of diff) {
        validateSequenceOp(line, d);
      }
    }
  }
}

/**
 * Remove the merge source indicator from a diff (returns a copy).
 */
export function stripSource(diff: IDiffEntry[] | null): IDiffEntry[] | null {
  if (!diff) {
    return null;
  }
  let ret: IDiffEntry[] = [];
  for (let e of diff) {
    if (e.op === 'patch') {
      ret.push({
        key: e.key,
        op: e.op,
        diff: stripSource(e.diff),
      });
    } else {
      let d = shallowCopy(e);
      delete d.source;
      ret.push(d);
    }
  }
  return ret;
}

/**
 * Translates a diff of strings split by str.splitlines() to a diff of the
 * joined multiline string
 */
export function flattenStringDiff(
  val: string[] | string,
  diff: IDiffArrayEntry[],
): IDiffArrayEntry[] {
  if (typeof val === 'string') {
    val = splitLines(val);
  }
  let lineToChar = [0].concat(accumulateLengths(val));
  let flattened: IDiffArrayEntry[] = [];
  for (let e of diff) {
    // Frist validate op:
    validateStringDiff(val, e, lineToChar);
    let lineOffset = lineToChar[e.key];
    if (e.op === 'patch') {
      let pdiff = e.diff as IDiffArrayEntry[];
      if (pdiff !== null) {
        for (let p of pdiff) {
          let d = shallowCopy(p);
          d.key += lineOffset;
          flattened.push(d);
        }
      }
    } else {
      // Other ops simply have keys which refer to lines
      let d: IDiffEntry | null = null;
      if (e.op === 'addrange') {
        d = opAddRange(lineOffset, (e.valuelist as any[]).join(''));
      } else {
        // e.op === 'removerange'
        let idx = e.key + e.length;
        d = opRemoveRange(lineOffset, lineToChar[idx] - lineOffset);
      }
      d.source = e.source;
      flattened.push(d);
    }
  }
  // Finally, sort on key (leaving equal items in original order)
  // This is done since the original diffs are sorted deeper first!
  return sortByKey(flattened, 'key');
}
