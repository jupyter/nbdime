// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
'use strict';

import {
  ReadonlyJSONObject
} from '@phosphor/coreutils';

import {
  IIterator
} from '@phosphor/algorithm';

import {
  IDiffObjectEntry
} from '../diff/diffentries';

import {
  valueIn, unique
} from '../common/util';


export
class PatchObjectHelper implements IIterator<string> {
  constructor(base: ReadonlyJSONObject, diff: IDiffObjectEntry[] | null) {
      this._diffLUT = {};
      let diffKeys : string[] = [];
      if (diff) {
        for (let d of diff) {
          diffKeys.push(d.key);
          this._diffLUT[d.key] = d;
        }
      }
      this._diffKeys = diffKeys;
      this.baseKeys = _objectKeys(base);
  }

  isDiffKey(key: string): boolean {
    return valueIn(key, this._diffKeys);
  }

  getDiffEntry(key: string): IDiffObjectEntry {
    return this._diffLUT[key];
  }

  /**
   * Whether there any dict entries after the current add/remove diff op.
   *
   * Note that if the current op is a remove op, it does not take into
   * account any entries added below it. Similarly, if the current op is
   * an add op it does not take into account any entries that are
   * removed after it.
   *
   * Assumes current key is a diff key to either an add or remove op.
   * @returns {boolean}
   */
  entriesAfterCurrentAddRem(): boolean {
    if (this._currentIsAddition === undefined) {
      throw new Error('Current op is not an add or remove op');
    }
    // Check for unchanged entries after, or any changed entries
    // that are not of the OPPOSITE add/remove type:
    let oppositeOp = this._currentIsAddition ? 'remove' : 'add';
    for (let key of this._remainingKeys) {
      if (!valueIn(key, this._diffKeys)) {
        // There remains unchanged entries after
        return true;
      } else if (this._diffLUT[key].op !== oppositeOp) {
        // There remains entries that should not be ignored
        return true;
      }
    }
    return false;
  }

  iter(): IIterator<string> {
    this._remainingKeys = this.baseKeys.concat(this._diffKeys).filter(unique).sort();
    return this;
  }

  keys(): IIterator<string> {
    return this;
  }

  next(): string {
    let key = this._remainingKeys.shift();
    if (key && valueIn(key, this._diffKeys)) {
      let op = this._diffLUT[key].op;
      if (op === 'add') {
        this._currentIsAddition = true;
      } else if (op === 'remove') {
        this._currentIsAddition = false;
      } else {
        this._currentIsAddition = undefined;
      }
    }
    // Cast as non-undefined as phosphor doesn't support strict null checks yet:
    return key!;
  }

  clone(): IIterator<string> {
    let c = new PatchObjectHelper({}, null);
    c.baseKeys = this.baseKeys;
    c._diffKeys = this._diffKeys;
    c._currentIsAddition = this._currentIsAddition;
    c._diffLUT = this._diffLUT;
    c._remainingKeys = this._remainingKeys.slice();
    return c;
  }

  baseKeys: string[];

  private _currentIsAddition: boolean | undefined;
  private _diffKeys: string[];
  private _diffLUT: { [key: string]: IDiffObjectEntry};
  private _remainingKeys: string[];
}


/**
 * The keys present in a Object class. Equivalent to Object.keys, but with a
 * fallback if not defined.
 */
let _objectKeys = Object.keys || function (obj: any): string[] {
  let has = Object.prototype.hasOwnProperty || function () { return true; };
  let keys: string[] = [];
  for (let key in obj) {
    if (has.call(obj, key)) {
      keys.push(key);
    }
  }
  return keys;
};
