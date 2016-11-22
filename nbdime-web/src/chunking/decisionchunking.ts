
import {
  IDiffEntry, DiffCollection, IDiffArrayEntry, opRemoveRange
} from '../diff/diffentries';

import {
  MergeDecision, buildDiffs, pushPath
} from '../merge/decisions';

import {
  hasEntries, valueIn, unique
} from '../common/util';


export
type MergeChunk = {baseStart: number, baseEnd: number, diffs: DiffCollection}


function anyDiffs(diffs: DiffCollection): boolean {
  for (let d of diffs) {
    if (hasEntries(d)) {
      return true;
    }
  }
  return false;
}

function getSectionBoundaries(diffs: IDiffArrayEntry[]) {
  let boundaries: number[] = [];
  for (let e of diffs) {
    let j = e.key;
    let k: number;
    boundaries.push(j);
    if (e.op === 'addrange') {
      // Pass
    } else if (e.op === 'removerange') {
      k = j + e.length;
      boundaries.push(k);
    } else if (e.op === 'patch') {
      k = j + 1;
      boundaries.push(k);
    }
  }
  return boundaries.filter(unique);
}


function splitDiffsOnBoundaries(diffs: IDiffArrayEntry[], boundaries: number[]): IDiffArrayEntry[] {
  let newdiffs: IDiffArrayEntry[] = [];
  if (!Array.isArray(boundaries)) {
    throw new Error();
  }

  // Next relevant boundary index
  let b = 0;

  for (let e of diffs) {
    if (valueIn(e.op, ['addrange', 'patch'])) {
      // Nothing to split
      newdiffs.push(e);
    } else if (e.op === 'removerange') {
      // Skip boundaries smaller than key
      while (boundaries[b] < e.key) {
        b += 1;
      }

      // key should be included in the boundaries
      if (boundaries[b] !== e.key) {
        throw new Error();
      }

      // Add diff entries for each interval between boundaries up to k
      while (b < boundaries.length - 1 && boundaries[b + 1] <= e.key + e.length) {
        newdiffs.push(opRemoveRange(boundaries[b],
                                    boundaries[b + 1] - boundaries[b]));
        b += 1;
      }
    } else {
      throw new Error('Unhandled diff entry op ' + e.op);
    }
  }

  return newdiffs;
}


/**
 * Make list of chunks on the form (j, k, diffs0, diffs1, ..., diffsN),
 * where `j` and `k` are line numbers in the base, and the `diffsX`
 * entries are subsets from `diffs` that are part of the chunk.

 * Because the diff entries have been split on the union of
 * begin/end boundaries of all diff entries, the keys of
 * diff entries on each side will always match a boundary
 * exactly. The only situation where multiple diff entries
 * on one side matches a boundary is when add/remove or
 * add/patch pairs occur, i.e. when inserting something
 * just before an item that is removed or modified.
 */
function makeChunks(boundaries: number[], diffs: DiffCollection): MergeChunk[] {
  let iDiffs: number[] = Array.apply(null, Array(diffs.length)).map(Number.prototype.valueOf, 0);
  let chunks: MergeChunk[] = [];
  for (let i=0; i < boundaries.length; ++i) {
    // Find span of next chunk
    let j = boundaries[i];
    let k = (i < boundaries.length - 1) ? boundaries[i + 1] : j;
    // Collect diff entries from each side
    // starting at beginning of this chunk
    let subDiffs: DiffCollection = [];
    for (let m=0; m < diffs.length; ++m) {
      let d = diffs[m];
      let dis: IDiffEntry[] = [];
      while (d && iDiffs[m] < d.length && d[iDiffs[m]].key === j) {
        dis.push(d[iDiffs[m]]);
        iDiffs[m] += 1;
      }
      subDiffs.push(dis);
    }
    // Add non-empty chunks
    if (anyDiffs(subDiffs)) {
      let c = {baseStart: j, baseEnd: k, diffs: subDiffs};
      chunks.push(c);
    }
  }
  return chunks;
}


/**
 * Return list of chunks (i, j, d0, d1, ..., dn) where dX are
 *  lists of diff entries affecting the range base[i:j].
 *
 *  If d0 and d1 are both empty the chunk is not modified.
 *
 *  Includes full range 0:len(base).
 *
 *  Each diff list contains either 0, 1, or 2 entries,
 *  in case of 2 entries the first will be an insert
 *  at i (the beginning of the range) and the other a
 *  removerange or patch covering the full range i:j.
 */
function makeMergeChunks(base: any[], diffs: DiffCollection): MergeChunk[] {
  // Split diffs on union of diff entry boundaries such that
  // no diff entry overlaps with more than one other entry.
  // Including 0,N makes loop over chunks cleaner.
  let boundaries = [0, base.length];
  for (let d of diffs) {
    if (hasEntries(d)) {
      let newBoundaries = getSectionBoundaries(d as IDiffArrayEntry[]);
      boundaries = boundaries.concat(newBoundaries);
    }
  }
  boundaries = boundaries.filter(unique).sort();
  let splitDiffs: DiffCollection = [];
  for (let d of diffs) {
    if (hasEntries(d)) {
      splitDiffs.push(splitDiffsOnBoundaries(d as IDiffArrayEntry[], boundaries));
    } else {
      splitDiffs.push(d);
    }
  }

  // Make list of chunks on the form (j, k, diffs)
  let chunks = makeChunks(boundaries, splitDiffs);

  return chunks;
}

function splitDecisionByChunks(base: any[], decision: MergeDecision, chunks: MergeChunk[]): MergeDecision[] {
  if (chunks.length < 2) {
    return [decision];
  }
  let out: MergeDecision[] = [];
  for (let c of chunks) {
    let cd = decision.customDiff;
    if (hasEntries(cd)) {
      if (decision.localPath.length > 0) {
        cd = pushPath(cd, decision.localPath);
      }
      // Split custom diff according to chunk lines
      let boundaries =
        [0, base.length, c.baseStart, c.baseEnd].filter(unique).sort();
      cd = splitDiffsOnBoundaries(cd as IDiffArrayEntry[], boundaries);
    }
    out.push(new MergeDecision(
      decision.absolutePath.slice(),
      c.diffs[0],
      c.diffs[1],
      decision.action,
      decision.conflict
    ));
  }
  return out;
}


export
function splitMergeDecisionsOnChunks(base: any[], decisions: MergeDecision[]): MergeDecision[] {
  let out: MergeDecision[] = [];

  for (let md of decisions) {
    let diffs: DiffCollection = [
      buildDiffs(base, [md], 'local'),
      buildDiffs(base, [md], 'remote')
    ];
    let chunks = makeMergeChunks(base, diffs);
    out = out.concat(splitDecisionByChunks(base, md, chunks));
  }

  return out;
}
