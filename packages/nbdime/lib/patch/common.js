// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
'use strict';
Object.defineProperty(exports, "__esModule", { value: true });
exports.PatchObjectHelper = void 0;
const util_1 = require("../common/util");
class PatchObjectHelper {
    constructor(base, diff) {
        this._diffLUT = {};
        let diffKeys = [];
        if (diff) {
            for (let d of diff) {
                diffKeys.push(d.key);
                this._diffLUT[d.key] = d;
            }
        }
        this._diffKeys = diffKeys;
        this.baseKeys = _objectKeys(base);
    }
    isDiffKey(key) {
        return util_1.valueIn(key, this._diffKeys);
    }
    getDiffEntry(key) {
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
    entriesAfterCurrentAddRem() {
        if (this._currentIsAddition === undefined) {
            throw new Error('Current op is not an add or remove op');
        }
        // Check for unchanged entries after, or any changed entries
        // that are not of the OPPOSITE add/remove type:
        let oppositeOp = this._currentIsAddition ? 'remove' : 'add';
        for (let key of this._remainingKeys) {
            if (!util_1.valueIn(key, this._diffKeys)) {
                // There remains unchanged entries after
                return true;
            }
            else if (this._diffLUT[key].op !== oppositeOp) {
                // There remains entries that should not be ignored
                return true;
            }
        }
        return false;
    }
    iter() {
        this._remainingKeys = this.baseKeys.concat(this._diffKeys).filter(util_1.unique).sort();
        return this;
    }
    keys() {
        return this;
    }
    next() {
        let key = this._remainingKeys.shift();
        if (key && util_1.valueIn(key, this._diffKeys)) {
            let op = this._diffLUT[key].op;
            if (op === 'add') {
                this._currentIsAddition = true;
            }
            else if (op === 'remove') {
                this._currentIsAddition = false;
            }
            else {
                this._currentIsAddition = undefined;
            }
        }
        return key;
    }
    clone() {
        let c = new PatchObjectHelper({}, null);
        c.baseKeys = this.baseKeys;
        c._diffKeys = this._diffKeys;
        c._currentIsAddition = this._currentIsAddition;
        c._diffLUT = this._diffLUT;
        c._remainingKeys = this._remainingKeys.slice();
        return c;
    }
}
exports.PatchObjectHelper = PatchObjectHelper;
/**
 * The keys present in a Object class. Equivalent to Object.keys, but with a
 * fallback if not defined.
 */
let _objectKeys = Object.keys || function (obj) {
    let has = Object.prototype.hasOwnProperty || function () { return true; };
    let keys = [];
    for (let key in obj) {
        if (has.call(obj, key)) {
            keys.push(key);
        }
    }
    return keys;
};
//# sourceMappingURL=common.js.map