// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
'use strict';
Object.defineProperty(exports, "__esModule", { value: true });
exports.patchString = exports.patchStringified = exports.stringifyAndBlankNull = exports.stringify = void 0;
const algorithm_1 = require("@lumino/algorithm");
const util_1 = require("../common/util");
const util_2 = require("../diff/util");
const diffentries_1 = require("../diff/diffentries");
const range_1 = require("../diff/range");
const common_1 = require("./common");
const stableStringify = require("json-stable-stringify");
/**
 * Ordered stringify. Wraps stableStringify(), but handles indentation.
 *
 * indentFirst controls whether the first line is indented as well, and
 * defaults to true.
 */
function stringify(values, level, indentFirst = true) {
    let ret = stableStringify(values, { space: util_2.JSON_INDENT });
    if (level) {
        ret = _indent(ret, level, indentFirst);
    }
    return ret;
}
exports.stringify = stringify;
/**
 * Ensure value is string, if not stringify.
 */
function stringifyAndBlankNull(value) {
    if (typeof value === 'string') {
        return value;
    }
    else if (value === null) {
        return '';
    }
    else {
        return stringify(value);
    }
}
exports.stringifyAndBlankNull = stringifyAndBlankNull;
/**
 * Patch a stringified JSON object.
 *
 * Returns the stringified value of the patched JSON object, as well as
 * position ranges indicating which parts of the string that was added or
 * removed.
 *
 * Internally, this builds the ranges based on the actual supplied diff, which
 * can therefore differ from a straigh string-based diff of stringified JSON
 * objects.
 */
function patchStringified(base, diff, level) {
    if (level === undefined) {
        level = 0;
    }
    if (typeof base === 'string') {
        // Only stringify if level > 0
        let stringifyPatch = level > 0;
        return patchString(base, diff, level, stringifyPatch);
    }
    else if (Array.isArray(base)) {
        return patchStringifiedList(base, diff, level);
    }
    else if (typeof base === 'number' || typeof base === 'boolean') {
        throw new TypeError('Cannot patch an atomic type: ' + typeof base);
    }
    else if (base === null) {
        throw new TypeError('Cannot patch a null base!');
    }
    else {
        return patchStringifiedObject(base, diff, level);
    }
}
exports.patchStringified = patchStringified;
/**
 * Patch a string according to a line based diff
 */
function patchString(base, diff, level, stringifyPatch) {
    let additions = [];
    let deletions = [];
    let baseIndex = 0;
    // Short-circuit if diff is empty
    if (diff === null) {
        return { remote: stringifyPatch ? stringify(base, level) : base,
            additions: additions,
            deletions: deletions };
    }
    // Diffs are line-based, so flatten to character based:
    diff = util_2.flattenStringDiff(base, diff);
    // Index into obj, the next item to take unless diff says otherwise
    let take = 0;
    let skip = 0;
    let remote = '';
    for (let e of diff) {
        let index = e.key;
        // Take values from obj not mentioned in diff, up to not including index
        let unchanged = base.slice(take, index);
        remote += unchanged;
        baseIndex += unchanged.length;
        if (e.op === 'addrange') {
            let added = e.valuelist;
            additions.push(new range_1.DiffRangeRaw(remote.length, added.length, e.source));
            remote += added;
            skip = 0;
        }
        else if (e.op === 'removerange') {
            // Delete a number of values by skipping
            skip = e.length;
            deletions.push(new range_1.DiffRangeRaw(baseIndex, skip, e.source));
            baseIndex += skip;
        }
        take = Math.max(take, index + skip);
    }
    remote += base.slice(take, base.length);
    if (stringifyPatch) {
        // The remote string should be stringified
        remote = stringify(remote, level);
        // Shift all indices by indentation + one to account for opening quote
        _offsetRanges(level * util_2.JSON_INDENT.length + 1, additions, deletions);
        // Offset ranges by JSON escaping
        _adjustRangesByJSONEscapes(remote, additions);
        _adjustRangesByJSONEscapes(stringify(base, level), deletions);
    }
    return { remote: remote, additions: additions, deletions: deletions };
}
exports.patchString = patchString;
/**
 * Patch a stringified object according to the object diff
 */
function patchStringifiedObject(base, diff, level) {
    let remote = '';
    let additions = [];
    let deletions = [];
    let postfix = ',\n';
    let baseIndex = 0;
    // Short-circuit if diff is empty
    if (diff === null) {
        return { remote: stringify(base, level),
            additions: additions,
            deletions: deletions };
    }
    // Object is dict. As diff keys should be unique, create map for easy processing
    let helper = new common_1.PatchObjectHelper(base, diff);
    let baseKeys = helper.baseKeys.slice();
    algorithm_1.each(helper.keys(), key => {
        let keyString = _makeKeyString(key, level + 1);
        if (helper.isDiffKey(key)) {
            // Entry has a change
            let e = helper.getDiffEntry(key);
            // Check for valid entry first:
            diffentries_1.validateObjectOp(base, e, baseKeys);
            if (util_1.valueIn(e.op, ['add', 'replace', 'remove'])) {
                // Replace is simply an add + remove, but without modifying keystring
                let isReplace = e.op === 'replace';
                if (e.op === 'add' || e.op === 'replace') {
                    let valr = stringify(e.value, level + 1, false) +
                        postfix;
                    let start = remote.length;
                    let length = valr.length;
                    // Modify range depending on add or replace:
                    if (isReplace) {
                        start += keyString.length;
                    }
                    else {
                        length += keyString.length;
                    }
                    // Check if postfix should be included or not
                    if (isReplace || !helper.entriesAfterCurrentAddRem()) {
                        length -= postfix.length;
                        if (e.op === 'add') {
                            length += 1; // Newline will still be added
                        }
                    }
                    additions.push(new range_1.DiffRangeRaw(start, length, e.source));
                    remote += keyString + valr;
                }
                if (e.op === 'remove' || e.op === 'replace') {
                    let valb = stringify(base[key], level + 1, false) + postfix;
                    let start = baseIndex;
                    let length = valb.length;
                    // Modify range depending on remove or replace:
                    if (isReplace) {
                        start += keyString.length;
                    }
                    else {
                        length += keyString.length;
                    }
                    // Check if postfix should be included or not
                    if (isReplace || !helper.entriesAfterCurrentAddRem()) {
                        length -= postfix.length;
                        if (e.op === 'remove') {
                            length += 1; // Newline will still be removed
                        }
                    }
                    deletions.push(new range_1.DiffRangeRaw(start, length, e.source));
                    baseIndex += keyString.length + valb.length;
                    baseKeys.splice(baseKeys.indexOf(key), 1);
                }
            }
            else if (e.op === 'patch') {
                let pd = patchStringified(base[key], e.diff, level + 1);
                let valr = pd.remote;
                // Insert key string:
                valr = keyString + valr.slice((level + 1) * util_2.JSON_INDENT.length) +
                    postfix;
                let offset = remote.length + keyString.length -
                    (level + 1) * util_2.JSON_INDENT.length;
                _offsetRanges(offset, pd.additions, pd.deletions);
                remote += valr;
                additions = additions.concat(pd.additions);
                deletions = deletions.concat(pd.deletions);
                baseIndex += stringify(base[key], level + 1, false).length +
                    keyString.length + postfix.length;
                baseKeys.splice(baseKeys.indexOf(key), 1);
            }
        }
        else {
            // Entry unchanged
            let val = keyString + stringify(base[key], level + 1, false) + postfix;
            remote += val;
            baseIndex += val.length;
        }
    });
    // Stringify correctly
    if (remote.slice(remote.length - postfix.length) === postfix) {
        remote = remote.slice(0, remote.length - postfix.length);
    }
    let indent = util_1.repeatString(util_2.JSON_INDENT, level);
    remote = indent + '{\n' + remote + '\n' + indent + '}';
    _offsetRanges(indent.length + 2, additions, deletions);
    return { remote: remote, additions: additions, deletions: deletions };
}
/**
 * Patch a stringified list according to the list diff
 */
function patchStringifiedList(base, diff, level) {
    let remote = '';
    let additions = [];
    let deletions = [];
    let baseIndex = 0; // Position in base string
    let postfix = ',\n';
    // Short-circuit if diff is empty
    if (diff === null) {
        return { remote: stringify(base, level),
            additions: additions,
            deletions: deletions };
    }
    // Index into obj, the next item to take unless diff says otherwise
    let take = 0;
    let skip = 0;
    for (let e of diff) {
        // Check for valid entry first:
        diffentries_1.validateSequenceOp(base, e);
        let index = e.key;
        // Take values from obj not mentioned in diff, up to not including index
        for (; index > take; take++) {
            let unchanged = stringify(base[take], level + 1) + postfix;
            remote += unchanged;
            baseIndex += unchanged.length;
        }
        if (e.op === 'addrange') {
            // Extend with new values directly
            let val = '';
            for (let v of e.valuelist) {
                val += stringify(v, level + 1) + postfix;
            }
            let difflen = val.length;
            if (index === base.length) {
                difflen -= 1; // No comma if at end
            }
            additions.push(new range_1.DiffRangeRaw(remote.length, difflen, e.source));
            remote += val;
            skip = 0;
        }
        else if (e.op === 'removerange') {
            // Delete a number of values by skipping
            let val = '';
            let len = e.length;
            for (let i = index; i < index + len; i++) {
                val += stringify(base[i], level + 1) + postfix;
            }
            let difflen = val.length;
            if (len + index === base.length) {
                difflen -= 1; // No comma if at end
            }
            deletions.push(new range_1.DiffRangeRaw(baseIndex, difflen, e.source));
            baseIndex += val.length;
            skip = e.length;
        }
        else if (e.op === 'patch') {
            let pd = patchStringified(base[index], e.diff, level + 1);
            skip = 1;
            let val = pd.remote + postfix;
            _offsetRanges(remote.length, pd.additions, pd.deletions);
            additions = additions.concat(pd.additions);
            deletions = deletions.concat(pd.deletions);
            baseIndex += stringify(base[index], level + 1).length;
            remote += val;
        }
        // Skip the specified number of elements, but never decrement take.
        // Note that take can pass index in diffs with repeated +/- on the
        // same index, i.e. [op_remove(index), op_add(index, value)]
        take = Math.max(take, index + skip);
    }
    // Take unchanged values at end
    for (; base.length > take; take++) {
        remote += stringify(base[take], level + 1) + postfix;
    }
    // Stringify correctly
    if (remote.slice(remote.length - postfix.length) === postfix) {
        remote = remote.slice(0, remote.length - postfix.length);
    }
    let indent = util_1.repeatString(util_2.JSON_INDENT, level);
    remote = indent + '[\n' + remote + '\n' + indent + ']';
    _offsetRanges(indent.length + 2, additions, deletions);
    return { remote: remote, additions: additions, deletions: deletions };
}
// Utility functions and variables:
/**
 * Indent a (multiline) string with `JSON_INDENT` given number of times.
 *
 * indentFirst controls whether the first line is indented as well.
 */
function _indent(str, levels, indentFirst) {
    indentFirst = indentFirst !== false;
    let lines = str.split('\n');
    let ret = new Array(lines.length);
    if (!indentFirst) {
        ret[0] = lines[0];
    }
    for (let i = indentFirst ? 0 : 1; i < lines.length; i++) {
        ret[i] = util_1.repeatString(util_2.JSON_INDENT, levels) + lines[i];
    }
    return ret.join('\n');
}
/** Make a string for a stringified dict key, with indentation */
function _makeKeyString(key, level) {
    return util_1.repeatString(util_2.JSON_INDENT, level) + '"' + key + '": ';
}
/** Shift all positions in given ranges by same amount */
function _offsetRanges(offset, additions, deletions) {
    for (let a of additions) {
        a.offset(offset);
    }
    for (let d of deletions) {
        d.offset(offset);
    }
}
/**
 * Adjust diff ranges to compensate for increased length occupied by characters
 * escaped during JSON stringification.
 */
function _adjustRangesByJSONEscapes(jsonString, ranges) {
    // First find all escaped characters, and expansion coefficients
    let simpleEscapes = [
        '\\\"', '\\\\', '\\/', '\\b', '\\f', '\\n', '\\r', '\\t'
    ];
    let surrogateUnicodes = /\\uD[89A-Fa-f][0-9a-fA-F]{2}\\uD[c-fC-F][0-9a-fA-F]{2}/g;
    // Look for unicodes that are not part of a surrogate:
    let unicodes = /(?!\\uD[c-fC-F][0-9a-fA-F]{2})\\u(?!D[89A-Fa-f][0-9a-fA-F]{2})\d{4}/g;
    const SIMPLE_ESCAPE_LENGTH = 2;
    const UNICODE_ESCAPE_LENGTH = 6;
    const SURROGATE_ESCAPE_LENGTH = 12;
    // Equal sized arrays identifying location and expansion
    // factor of each escaped character:
    let indices = [];
    let expansions = [];
    for (let e of simpleEscapes) {
        let len = JSON.parse('"' + e + '"').length;
        let i = 0;
        while (1) {
            i = jsonString.indexOf(e, i);
            if (i < 0) {
                break;
            }
            indices.push(i);
            expansions.push(SIMPLE_ESCAPE_LENGTH - len);
            i++;
        }
    }
    let match;
    while ((match = unicodes.exec(jsonString)) !== null) {
        indices.push(match.index);
        expansions.push(UNICODE_ESCAPE_LENGTH -
            JSON.parse('"' + match[0] + '"').length);
    }
    while ((match = surrogateUnicodes.exec(jsonString)) !== null) {
        indices.push(match.index);
        expansions.push(SURROGATE_ESCAPE_LENGTH -
            JSON.parse('"' + match[0] + '"').length);
    }
    // Now adjust differences
    // TODO: Optimize this algorithm?
    for (let i = 0; i < indices.length; i++) {
        for (let r of ranges) {
            let idx = indices[i];
            let exp = expansions[i];
            if (r.from > idx) {
                r.from += exp;
            }
            if (r.to > idx) {
                r.to += exp;
            }
        }
    }
}
//# sourceMappingURL=stringified.js.map