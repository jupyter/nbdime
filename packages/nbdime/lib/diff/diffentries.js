// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
'use strict';
Object.defineProperty(exports, "__esModule", { value: true });
exports.validateObjectOp = exports.validateSequenceOp = exports.opPatch = exports.opRemoveRange = exports.opAddRange = exports.opRemove = exports.opAdd = exports.opReplace = void 0;
const util_1 = require("../common/util");
/** Create a replacement diff entry */
function opReplace(key, value) {
    return { op: 'replace', key: key, value: value };
}
exports.opReplace = opReplace;
/** Create an addition diff entry */
function opAdd(key, value) {
    return { op: 'add', key: key, value: value };
}
exports.opAdd = opAdd;
/** Create a removal diff entry */
function opRemove(key) {
    return { op: 'remove', key: key };
}
exports.opRemove = opRemove;
/** Create a removal diff entry */
function opAddRange(key, valuelist) {
    return { op: 'addrange', key: key, valuelist: valuelist };
}
exports.opAddRange = opAddRange;
/** Create a range removal diff entry */
function opRemoveRange(key, length) {
    return { op: 'removerange', key: key, length: length };
}
exports.opRemoveRange = opRemoveRange;
/** Create a range removal diff entry */
function opPatch(key, diff) {
    return { op: 'patch', key: key, diff: diff };
}
exports.opPatch = opPatch;
/**
 * Validate that a diff operation is valid to apply on a given base sequence
 */
function validateSequenceOp(base, entry) {
    if (typeof entry.key !== 'number') {
        console.info('Invalid patch details', base, entry);
        throw new TypeError(`Invalid patch sequence op: Key is not a number: ${entry.key}`);
    }
    let index = entry.key;
    if (entry.op === 'addrange') {
        if (index < 0 || index > base.length || isNaN(index)) {
            throw new RangeError('Invalid add range diff op: Key out of range: ' + index);
        }
    }
    else if (entry.op === 'removerange') {
        if (index < 0 || index >= base.length || isNaN(index)) {
            throw new RangeError('Invalid remove range diff op: Key out of range: ' + index);
        }
        let skip = entry.length;
        if (index + skip > base.length || isNaN(index)) {
            throw new RangeError('Invalid remove range diff op: Range too long!');
        }
    }
    else if (entry.op === 'patch') {
        if (index < 0 || index >= base.length || isNaN(index)) {
            throw new RangeError('Invalid patch diff op: Key out of range: ' + index);
        }
    }
    else {
        throw new Error('Invalid op: ' + entry.op);
    }
}
exports.validateSequenceOp = validateSequenceOp;
/**
 * Validate that a diff operation is valid to apply on a given base object
 */
function validateObjectOp(base, entry, keys) {
    let op = entry.op;
    if (typeof entry.key !== 'string') {
        console.info('Invalid patch details', base, entry, keys);
        throw new TypeError(`Invalid patch object op: Key is not a string: ${entry.key}`);
    }
    let key = entry.key;
    if (op === 'add') {
        if (util_1.valueIn(key, keys)) {
            throw new Error('Invalid add key diff op: Key already present: ' + key);
        }
    }
    else if (op === 'remove') {
        if (!util_1.valueIn(key, keys)) {
            throw new Error('Invalid remove key diff op: Missing key: ' + key);
        }
    }
    else if (op === 'replace') {
        if (!util_1.valueIn(key, keys)) {
            throw new Error('Invalid replace key diff op: Missing key: ' + key);
        }
    }
    else if (op === 'patch') {
        if (!util_1.valueIn(key, keys)) {
            throw new Error('Invalid patch key diff op: Missing key: ' + key);
        }
    }
    else {
        throw new Error('Invalid op: ' + op);
    }
}
exports.validateObjectOp = validateObjectOp;
//# sourceMappingURL=diffentries.js.map