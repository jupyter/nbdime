// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
'use strict';

import {
  sortByKey, shallowCopy, accumulateLengths, splitLines
} from '../common/util';

import {
  ChunkSource
} from '../chunking';

import {
  IDiffEntry, IDiffArrayEntry, IDiffPatch, IDiffAddRange, IDiffRemoveRange,
  opAddRange, opRemoveRange, validateSequenceOp
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
function getSubDiffByKey(diff: IDiffEntry[] | null, key: string | number) : IDiffEntry[] | null {
  if (!diff) {
    return null;
  }
  for (let i=0; i < diff.length; ++i) {
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
export
function getDiffEntryByKey(diff: IDiffEntry[] | null, key: string | number) : IDiffEntry | null {
  if (!diff) {
    return null;
  }
  for (let i=0; i < diff.length; ++i) {
    if (diff[i].key === key) {
      return diff[i];
    }
  }
  return null;
}


function validateStringDiff(base: string[], entry: IDiffArrayEntry, lineToChar: number[]): void {
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


function areSourcesCompatible(a: ChunkSource | undefined, b: ChunkSource | undefined): boolean {
  if (!a || !b || a === b) {
    return true;
  }
  if (a.decision === b.decision) {
    // 'either' sources can be combined with local or remote
    if (a.action === 'either' && b.action !== 'custom' ||
        b.action === 'either' && a.action !== 'custom') {
      return true;
    }
  }
  return false;
}

/**
 * Remove the merge source indicator from a diff (returns a copy).
 */
export
function stripSource(diff: IDiffEntry[] | null): IDiffEntry[] | null {
  if (!diff) {
    return null;
  }
  let ret: IDiffEntry[] = [];
  for (let e of diff) {
    if (e.op === 'patch') {
      ret.push({
        key: e.key,
        op: e.op,
        diff: stripSource(e.diff)
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
 * Check whether existing collection of diff ops shares a key with the new
 * diffop, and if they  also have the same op type.
 */
function overlaps(existing: IDiffArrayEntry[], newv: IDiffArrayEntry): number {
  if (existing.length < 1) {
    return -1;
  }
  for (let i=0; i < existing.length; ++i) {
    let e = existing[i];
    if (!areSourcesCompatible(e.source, newv.source)) {
      continue;
    }
    if (e.op === newv.op) {
      if (e.op === 'removerange') {
        // Since patch ops of lines come before line add/remove
        // (and patch ops can contain character removals),
        // we need to check order:
        let first = e.key <= newv.key ? e : newv as IDiffRemoveRange;
        let last = e.key <= newv.key ? newv as IDiffRemoveRange : e;
        if (first.key + first.length >= last.key) {
          // Overlapping deletes
          // Above check is open ended to allow for sanity check here:
          if (first.key + first.length !== last.key) {
            throw new Error('Overlapping delete diff ops: ' +
              'Two operation remove same characters!');
          }
          return i;
        }
      } else if (e.key === newv.key) {
        // Found a match
        return i;
      } else if (e.op === 'addrange') {
        // Check if there is a removerange after the
        // addrange that will cause the two addranges
        // to abut.
        if (i < existing.length - 1) {
          let other = existing[i + 1];
          if (other.op === 'removerange' &&
              other.key === e.key &&
              other.key + other.length === newv.key) {
            return i;
          }
        }
      }
    }
  }
  return -1;
}


/**
 * Combines two ops into a new one that does the same
 */
function combineOps(a: IDiffArrayEntry, b: IDiffArrayEntry): IDiffAddRange | IDiffRemoveRange {
  let combined: IDiffArrayEntry;
  if (b.op === 'addrange') {
    combined = opAddRange(a.key, (a as IDiffAddRange).valuelist);
    // valuelist can also be string, but string also has concat:
    combined.valuelist = (combined.valuelist as any[]).concat(b.valuelist as any[]);
  } else if (b.op === 'removerange') {
    if (a.op !== 'removerange') {
      throw new Error('Cannot combine operations: ' + a + ', ' + b);
    }
    combined = opRemoveRange(a.key, a.length + b.length);
  } else {
    throw new Error('Invalid string lines op to combine: ' + b);
  }
  combined.source = a.source;
  if (!areSourcesCompatible(a.source, b.source)) {
    throw new Error('Cannot combine diff ops with incompatible sources in one string line');
  }
  return combined;
}


/**
 * Translates a diff of strings split by str.splitlines() to a diff of the
 * joined multiline string
 */
export
function flattenStringDiff(val: string[] | string, diff: IDiffArrayEntry[]): IDiffArrayEntry[] {

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
          let idx = overlaps(flattened, d);
          if (idx >= 0) {
            flattened[idx] = combineOps(flattened[idx], d);
          } else {
            flattened.push(d);
          }
        }
      }
    } else {
      // Other ops simply have keys which refer to lines
      let d: IDiffEntry | null = null;
      if (e.op === 'addrange') {
        d = opAddRange(lineOffset,
                       (e.valuelist as any[]).join(''));
      } else { // e.op === 'removerange'
        let idx = e.key + e.length;
        d = opRemoveRange(lineOffset,
                          lineToChar[idx] - lineOffset);
      }
      d.source = e.source;

      let idx = overlaps(flattened, d);
      if (idx >= 0) {
        flattened[idx] = combineOps(flattened[idx], d);
      } else {
        flattened.push(d);
      }
    }
  }
  // Finally, sort on key (leaving equal items in original order)
  // This is done since the original diffs are sorted deeper first!
  return sortByKey(flattened, 'key');
}
