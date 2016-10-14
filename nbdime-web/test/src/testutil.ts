// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.

import {
  shallowCopy
} from '../../src/common/util';

import {
  IDiffEntry
} from '../../src/diff/diffentries';


/**
 * Remove the merge source indicator from a diff (returns a copy).
 *
 * Useful for isolating tests that look on other things.
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