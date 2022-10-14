// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
'use strict';
Object.defineProperty(exports, "__esModule", { value: true });
exports.flattenStringDiff = exports.stripSource = exports.getDiffEntryByKey = exports.getSubDiffByKey = exports.JSON_INDENT = void 0;
const util_1 = require("../common/util");
const diffentries_1 = require("./diffentries");
/**
 * The indentation to use for JSON stringify.
 */
exports.JSON_INDENT = '  ';
/**
 * Search the list of diffs for an entry with the given key.
 *
 * Returns the first found entry, or null if not entry was found.
 */
function getSubDiffByKey(diff, key) {
    if (!diff) {
        return null;
    }
    for (let i = 0; i < diff.length; ++i) {
        if (diff[i].key === key) {
            return diff[i].diff || null;
        }
    }
    return null;
}
exports.getSubDiffByKey = getSubDiffByKey;
/**
 * Search the list of diffs for an entry with the given key.
 *
 * Returns the first found entry, or null if not entry was found.
 */
function getDiffEntryByKey(diff, key) {
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
exports.getDiffEntryByKey = getDiffEntryByKey;
function validateStringDiff(base, entry, lineToChar) {
    // First valdiate line ops:
    diffentries_1.validateSequenceOp(base, entry);
    if (entry.op === 'patch') {
        let line = base[entry.key];
        let diff = entry.diff;
        if (diff !== null) {
            for (let d of diff) {
                diffentries_1.validateSequenceOp(line, d);
            }
        }
    }
}
/**
 * Remove the merge source indicator from a diff (returns a copy).
 */
function stripSource(diff) {
    if (!diff) {
        return null;
    }
    let ret = [];
    for (let e of diff) {
        if (e.op === 'patch') {
            ret.push({
                key: e.key,
                op: e.op,
                diff: stripSource(e.diff)
            });
        }
        else {
            let d = util_1.shallowCopy(e);
            delete d.source;
            ret.push(d);
        }
    }
    return ret;
}
exports.stripSource = stripSource;
/**
 * Translates a diff of strings split by str.splitlines() to a diff of the
 * joined multiline string
 */
function flattenStringDiff(val, diff) {
    if (typeof val === 'string') {
        val = util_1.splitLines(val);
    }
    let lineToChar = [0].concat(util_1.accumulateLengths(val));
    let flattened = [];
    for (let e of diff) {
        // Frist validate op:
        validateStringDiff(val, e, lineToChar);
        let lineOffset = lineToChar[e.key];
        if (e.op === 'patch') {
            let pdiff = e.diff;
            if (pdiff !== null) {
                for (let p of pdiff) {
                    let d = util_1.shallowCopy(p);
                    d.key += lineOffset;
                    flattened.push(d);
                }
            }
        }
        else {
            // Other ops simply have keys which refer to lines
            let d = null;
            if (e.op === 'addrange') {
                d = diffentries_1.opAddRange(lineOffset, e.valuelist.join(''));
            }
            else { // e.op === 'removerange'
                let idx = e.key + e.length;
                d = diffentries_1.opRemoveRange(lineOffset, lineToChar[idx] - lineOffset);
            }
            d.source = e.source;
            flattened.push(d);
        }
    }
    // Finally, sort on key (leaving equal items in original order)
    // This is done since the original diffs are sorted deeper first!
    return util_1.sortByKey(flattened, 'key');
}
exports.flattenStringDiff = flattenStringDiff;
//# sourceMappingURL=util.js.map