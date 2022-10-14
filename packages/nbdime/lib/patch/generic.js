// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
'use strict';
Object.defineProperty(exports, "__esModule", { value: true });
exports.patch = void 0;
const coreutils_1 = require("@lumino/coreutils");
const util_1 = require("../common/util");
const diffentries_1 = require("../diff/diffentries");
const stringified_1 = require("./stringified");
function patch(base, diff) {
    if (typeof base === 'string') {
        return stringified_1.patchString(base, diff, 0, false).remote;
    }
    else if (Array.isArray(base)) {
        const baseCopy = coreutils_1.JSONExt.deepCopy(base);
        return patchSequence(baseCopy, diff);
    }
    else if (typeof base === 'number' || typeof base === 'boolean') {
        throw new TypeError('Cannot patch an atomic type: ' + typeof base);
    }
    else if (base === null) {
        throw new TypeError('Cannot patch a null base!');
    }
    else {
        const baseCopy = coreutils_1.JSONExt.deepCopy(base);
        return patchObject(baseCopy, diff);
    }
}
exports.patch = patch;
/**
 * Patch an array according to the diff.
 */
function patchSequence(base, diff) {
    if (diff === null) {
        return util_1.deepCopy(base);
    }
    // The patched sequence to build and return
    let patched = [];
    // Index into obj, the next item to take unless diff says otherwise
    let take = 0;
    let skip = 0;
    for (let e of diff) {
        // Check for valid entry first:
        diffentries_1.validateSequenceOp(base, e);
        let index = e.key;
        // Take values from base not mentioned in diff, up to not including
        // index
        for (let value of base.slice(take, index)) {
            patched.push(util_1.deepCopy(value));
        }
        if (e.op === 'addrange') {
            // Extend with new values directly
            patched = patched.concat(e.valuelist);
            skip = 0;
        }
        else if (e.op === 'removerange') {
            // Delete a number of values by skipping
            skip = e.length;
        }
        else if (e.op === 'patch') {
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
        patched.push(util_1.deepCopy(value));
    }
    return patched;
}
/**
 * Patch an object (dictionary type) according to the diff.
 */
function patchObject(base, diff) {
    let patched = {};
    let keysToCopy = Object.keys(base);
    if (diff) {
        for (let e of diff) {
            // Check for valid entry first:
            diffentries_1.validateObjectOp(base, e, keysToCopy);
            let key = e.key;
            if (e.op === 'add') {
                patched[key] = e.value;
            }
            else if (e.op === 'remove') {
                keysToCopy.splice(keysToCopy.indexOf(key), 1); // Remove key
            }
            else if (e.op === 'replace') {
                keysToCopy.splice(keysToCopy.indexOf(key), 1); // Remove key
                patched[key] = e.value;
            }
            else if (e.op === 'patch') {
                keysToCopy.splice(keysToCopy.indexOf(key), 1); // Remove key
                patched[key] = patch(base[key], e.diff);
            }
        }
    }
    // Take items not mentioned in diff
    for (let key of keysToCopy) {
        patched[key] = util_1.deepCopy(base[key]);
    }
    return patched;
}
//# sourceMappingURL=generic.js.map