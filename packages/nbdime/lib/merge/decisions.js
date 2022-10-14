// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
// This code is based on the CodeMirror mergeview.js source:
// CodeMirror, copyright (c) by Marijn Haverbeke and others
// Distributed under an MIT license: http://codemirror.net/LICENSE
'use strict';
Object.defineProperty(exports, "__esModule", { value: true });
exports.filterDecisions = exports.pushPatchDecision = exports.buildDiffs = exports.applyDecisions = exports.resolveCommonPaths = exports.pushPath = exports.popPath = exports.addSorted = exports.decisionSortKey = exports.decisionPathSortKey = exports.MergeDecision = void 0;
const diffentries_1 = require("../diff/diffentries");
const util_1 = require("../diff/util");
const patch_1 = require("../patch");
const util_2 = require("../common/util");
function validateAction(action) {
    if (util_2.valueIn(action, ['base', 'local', 'remote', 'local_then_remote',
        'remote_then_local', 'custom', 'clear', 'clear_parent', 'either'])) {
        return action;
    }
    throw new Error('Invalid merge decision action: ' + action);
}
/**
 * Take the value, or take default if value is undefined
 */
function valueOrDefault(value, defaultValue) {
    return value === undefined ? defaultValue : value;
}
class MergeDecision {
    constructor(obj, localDiff = null, remoteDiff = null, action = 'base', conflict = false, customDiff = null, similarInsert = null) {
        this.level = 0;
        if (obj instanceof Array) {
            this._path = obj;
        }
        else if (obj instanceof MergeDecision) {
            this._path = obj.absolutePath.slice();
            localDiff = obj.localDiff;
            remoteDiff = obj.remoteDiff;
            action = obj.action;
            conflict = obj.conflict;
            customDiff = obj.customDiff;
            similarInsert = obj.similarInsert;
            this.level = obj.level;
        }
        else {
            this._path = valueOrDefault(obj.common_path, []);
            localDiff = valueOrDefault(obj.local_diff, localDiff);
            remoteDiff = valueOrDefault(obj.remote_diff, remoteDiff);
            action = validateAction(valueOrDefault(obj.action, action));
            conflict = valueOrDefault(obj.conflict, conflict);
            customDiff = valueOrDefault(obj.custom_diff, customDiff);
            similarInsert = valueOrDefault(obj.similar_insert, similarInsert);
        }
        this.localDiff = localDiff;
        this.remoteDiff = remoteDiff;
        this.action = action;
        this.conflict = conflict;
        this.customDiff = customDiff;
        this.similarInsert = similarInsert;
    }
    setValuesFrom(other) {
        this._path = other.absolutePath.slice();
        this.localDiff = other.localDiff;
        this.remoteDiff = other.remoteDiff;
        this.action = other.action;
        this.conflict = other.conflict;
        this.customDiff = other.customDiff;
        this.similarInsert = other.similarInsert;
        this.level = other.level;
    }
    get localPath() {
        return this._path.slice(this.level);
    }
    get absolutePath() {
        return this._path;
    }
    set absolutePath(value) {
        this._path = value;
    }
    pushPath(key) {
        this._path.push(key);
    }
    get diffs() {
        let diffs = [this.localDiff, this.remoteDiff];
        if (this.customDiff) {
            diffs.push(this.customDiff);
        }
        return diffs;
    }
    set diffs(value) {
        this.localDiff = value[0];
        this.remoteDiff = value[1];
        if (value.length > 2) {
            this.customDiff = value[2];
        }
    }
    serialize() {
        return {
            common_path: this.absolutePath.slice(),
            local_diff: util_1.stripSource(this.localDiff),
            remote_diff: util_1.stripSource(this.remoteDiff),
            action: this.action,
            conflict: this.conflict,
            custom_diff: util_1.stripSource(this.customDiff)
        };
    }
}
exports.MergeDecision = MergeDecision;
/**
 * Compare to DecisionPath's for sorting.
 *
 * The rules are that deeper paths sort before other paths
 * with the same prefix, as they correspond to patch ops,
 * which will not affect the indexing of following decisions
 * on lists.
 *
 * @param {DecisionPath} a The first decision path
 * @param {DecisionPath} b The second decision path
 * @returns {number} Returns a negative number if a should
 *  sort first, positive number if b should sort first, or
 *  zero if the are identical.
 */
function decisionPathSortKey(a, b) {
    if (a.length === b.length) {
        // Equally deep, sort on keys
        for (let lvl = 0; lvl < a.length; ++lvl) {
            if (a[lvl] === b[lvl]) {
                // Keys are equal, try a deeper level
                continue;
            }
            // Keys differ on this level!
            return a[lvl] < b[lvl] ? -1 : 1;
        }
        // Paths are identical
        return 0;
    }
    else {
        // Sort deeper paths first
        return b.length - a.length;
    }
}
exports.decisionPathSortKey = decisionPathSortKey;
/**
 * Compare the paths of two decisions for sorting.
 *
 * This is a thin wrapper around decisionPathSortKey
 *
 * @export
 * @param {MergeDecision} a The first decision
 * @param {MergeDecision} b The second decision
 * @returns {number}  Returns a negative number if a should
 *  sort first, positive number if b should sort first, or
 *  zero if the are identical.
 */
function decisionSortKey(a, b) {
    return decisionPathSortKey(a.absolutePath, b.absolutePath);
}
exports.decisionSortKey = decisionSortKey;
/**
 * Adds a decision to an existing, sorted collection of merge decisions
 *
 * Ensures that the location of the newly added decision
 * will comply with the format specification
 *
 * @export
 * @param {MergeDecision[]} decisions
 * @param {MergeDecision} toAdd
 * @param {(number | string)} [firstKey]
 * @returns {void}
 */
function addSorted(decisions, toAdd, firstKey) {
    let idx = 0;
    for (; idx < decisions.length; ++idx) {
        let c = decisionPathSortKey(decisions[idx].absolutePath, toAdd.absolutePath);
        if (c > 0) {
            decisions.splice(idx, 0, toAdd);
            return;
        }
        else if (firstKey !== undefined && c === 0) {
            let key = null;
            for (let diff of decisions[idx].diffs) {
                if (!diff) {
                    continue;
                }
                for (let d of diff) {
                    if (!key || d.key < key) {
                        key = d.key;
                    }
                }
            }
            if (firstKey === key) {
                throw new Error('Shouldn\'t have multiple decisions with diff on same key');
            }
            else if (key === null || firstKey < key) {
                decisions.splice(idx, 0, toAdd);
                return;
            }
        }
    }
    decisions.push(toAdd);
}
exports.addSorted = addSorted;
function popPath(diffs, popInner) {
    if (diffs.length < 1) {
        return null;
    }
    // Find first non-null, non-empty diff list:
    let i = 0;
    for (let di of diffs) {
        if (di !== null && di.length > 0) {
            break;
        }
        i++;
    }
    // Assert that we have at least one non-null diff:
    if (i === diffs.length) {
        console.log('Empty merge decision (no diffs)!');
        return null;
    }
    // Check if ops and keys are equal for all non-null diffs
    let d = diffs[i];
    let op = d[0].op;
    let key = d[0].key;
    for (let di of diffs) {
        if (di && di.length > 0) {
            // Note that while diff lists can have 2 entries, they should never cause
            // a pop, as they will have a difference in op.
            for (let dj of di) {
                if (dj.op !== op || dj.key !== key) {
                    return null;
                }
            }
        }
    }
    // Inspect patch op further along:
    if (op === 'patch') {
        // Only pop if sub-diff has length 1 (unless popInner is true)
        if (popInner !== true) {
            for (let di of diffs) {
                if (di && di.length > 0 && (di.length !== 1 ||
                    !di[0].diff ||
                    di[0].diff.length !== 1)) {
                    return null;
                }
            }
        }
        let retDiffs = [];
        for (let di of diffs) {
            if (di && di.length > 0) {
                retDiffs.push(di[0].diff);
            }
            else {
                retDiffs.push(null);
            }
        }
        return { diffs: retDiffs, key: key };
    }
    return null;
}
exports.popPath = popPath;
function pushPath(diffs, prefix) {
    for (let key of prefix.reverse()) {
        diffs = [diffentries_1.opPatch(key, diffs)];
    }
    return diffs;
}
exports.pushPath = pushPath;
/**
 * Expand the `common_path` field of the merge decisions for optimized
 * processing. Modifies the merge decisions in-place.
 */
function resolveCommonPaths(decisions) {
    for (let md of decisions) {
        let diffs = md.diffs;
        let path = md.absolutePath || [];
        let popped = popPath(diffs, true);
        while (popped) {
            path.push(popped.key);
            diffs = popped.diffs;
            popped = popPath(diffs, true);
        }
        md.absolutePath = path;
        md.diffs = diffs;
    }
}
exports.resolveCommonPaths = resolveCommonPaths;
/**
 * Make a new 'cleared' value of the right type.
 */
function makeClearedValue(value) {
    if (value instanceof Array) {
        // Clearing e.g. an outputs list means setting it to an empty array
        return [];
    }
    else if (typeof (value) === 'string') {
        // Clearing e.g. a source string means setting it to an empty string
        return '';
    }
    else if (value === null || util_2.valueIn(typeof (value), ['number', 'boolean'])) {
        // Clearing anything else (atomic values) means setting it to null
        return null;
    }
    else {
        // Clearing e.g. a metadata dict means setting it to an empty Object
        return {};
    }
}
function _resolvePathInObject(obj, path) {
    for (let key of path) {
        obj = obj[key]; // Should throw if key missing
    }
    return obj;
}
function _combineDiffs(a, b) {
    if (a && b) {
        return a.concat(b);
    }
    else if (a) {
        return a.slice();
    }
    else if (b) {
        return b.slice();
    }
    else {
        return [];
    }
}
function resolveAction(base, decision) {
    let a = decision.action;
    if (a === 'base') {
        return []; // no-op
    }
    else if (a === 'local' || a === 'either') {
        return decision.localDiff ? decision.localDiff.slice() : [];
    }
    else if (a === 'remote') {
        return decision.remoteDiff ? decision.remoteDiff.slice() : [];
    }
    else if (a === 'custom') {
        return decision.customDiff ? decision.customDiff.slice() : [];
    }
    else if (a === 'local_then_remote') {
        return _combineDiffs(decision.localDiff, decision.remoteDiff);
    }
    else if (a === 'remote_then_local') {
        return _combineDiffs(decision.remoteDiff, decision.localDiff);
    }
    else if (a === 'clear') {
        let key = null;
        if (typeof base !== 'object') {
            throw new TypeError('Can only use `\'clear\'` action on objects/dicts');
        }
        for (let d of _combineDiffs(decision.localDiff, decision.remoteDiff)) {
            if (key) {
                if (key !== d.key) {
                    throw new Error('Cannot combine diffs with different keys');
                }
            }
            else {
                key = d.key;
            }
        }
        if (key) {
            let d = diffentries_1.opReplace(key, makeClearedValue(base[key]));
            d.source = { decision, action: 'custom' };
            return [d];
        }
        else {
            return [];
        }
    }
    else if (a === 'clear_parent') {
        if (Array.isArray(base)) {
            let d = diffentries_1.opRemoveRange(0, base.length);
            d.source = { decision, action: 'custom' };
            return [d];
        }
        else if (typeof (base) === 'string') {
            let len = util_2.splitLines(base).length;
            let d = diffentries_1.opRemoveRange(0, len);
            d.source = { decision, action: 'custom' };
            return [d];
        }
        else {
            // Ideally we would do a opReplace on the parent, but this is not
            // easily combined with this method, so simply remove all keys
            let diff = [];
            for (let key of base) {
                let d = diffentries_1.opRemove(key);
                d.source = { decision, action: 'custom' };
                diff.push(d);
            }
            return diff;
        }
    }
    else {
        throw new Error('The action \"' + a + '\" is not defined');
    }
}
/**
 * Prevent paths from pointing to specific string lines.
 *
 * Check if path points to a specific line in a string, if so, split off index.
 *
 * Returns a tuple of path and any line key.
 */
function splitDiffStringPath(base, path) {
    for (let i = 0; i < path.length; ++i) {
        if (typeof base === 'string') {
            return [path.slice(0, i), path.slice(i)];
        }
        base = base[path[i]];
    }
    return [path, null];
}
function applyDecisions(base, decisions) {
    let merged = util_2.deepCopy(base);
    let prevPath = null;
    let parent = null;
    let lastKey = null;
    let resolved = null;
    let diffs = [];
    // clear_parent actions should override other decisions on same obj, so
    // we need to track it
    let clearParent = false;
    for (let md of decisions) {
        let spl = splitDiffStringPath(merged, md.localPath);
        let path = spl[0];
        let line = spl[1];
        // We patch all decisions with the same path in one op
        if (util_2.arraysEqual(path, prevPath)) {
            if (clearParent) {
                // Another entry will clear the parent, so all other decisions
                // should be dropped
            }
            else {
                if (md.action === 'clear_parent') {
                    clearParent = true;
                    diffs = []; // Clear any exisiting decsions!
                }
                let ad = resolveAction(resolved, md);
                if (line) {
                    ad = pushPath(ad, line);
                }
                diffs = diffs.concat(ad);
            }
        }
        else {
            // Different path, start a new collection
            if (prevPath !== null) {
                // First, apply previous diffs
                if (parent === null) {
                    // Operations on root create new merged object
                    merged = patch_1.patch(resolved, diffs);
                }
                else {
                    // If not, overwrite entry in parent (which is an entry in merged).
                    // This is ok, as no paths should point to subobjects of the patched
                    // object.
                    parent[lastKey] = patch_1.patch(resolved, diffs);
                }
            }
            prevPath = path.slice();
            // Resolve path in base and output
            resolved = merged;
            parent = null;
            lastKey = null;
            for (let key of path) {
                parent = resolved;
                resolved = resolved[key]; // Should throw if key missing
                lastKey = key;
            }
            diffs = resolveAction(resolved, md);
            if (line) {
                diffs = pushPath(diffs, line);
            }
            clearParent = md.action === 'clear_parent';
        }
    }
    // Apply the last collection of diffs, if present (same as above)
    if (prevPath !== null) {
        if (parent === null) {
            merged = patch_1.patch(resolved, diffs);
        }
        else {
            parent[lastKey] = patch_1.patch(resolved, diffs);
        }
    }
    return merged;
}
exports.applyDecisions = applyDecisions;
/**
 * Merge a tree of diffs at varying path levels to one diff at their shared root
 *
 * Relies on the format specification about decision ordering to help
 * simplify the process (deeper paths should come before its parent paths).
 * This is realized by the `sortedPaths` argument.
 */
function _mergeTree(tree, sortedPaths) {
    let trunk = [];
    let root = null;
    for (let i = 0; i < sortedPaths.length; ++i) {
        let path = tree[sortedPaths[i]].path;
        let subdiffs = tree[sortedPaths[i]].diff;
        trunk = trunk.concat(subdiffs);
        let nextPath;
        if (i === sortedPaths.length - 1) {
            nextPath = root;
        }
        else {
            nextPath = tree[sortedPaths[i + 1]].path;
        }
        // First, check if path is subpath of nextPath:
        if (util_2.isPrefixArray(nextPath, path)) {
            // We can simply promote existing diffs to next path
            if (nextPath !== null) {
                trunk = pushPath(trunk, path.slice(nextPath.length));
                root = nextPath;
            }
        }
        else {
            // We have started on a new trunk
            // Collect branches on the new trunk, and merge the trunks
            let newTrunk = _mergeTree(tree, sortedPaths.slice(i + 1));
            nextPath = tree[sortedPaths[sortedPaths.length - 1]].path;
            let prefix = util_2.findSharedPrefix(path, nextPath);
            let pl = prefix ? prefix.length : 0;
            trunk = pushPath(trunk, path.slice(pl)).concat(pushPath(newTrunk, nextPath.slice(pl)));
            break; // Recursion will exhaust sortedPaths
        }
    }
    return trunk;
}
/**
 * Builds a diff for direct application on base. The `which` argument either
 * selects the 'local', 'remote' or 'merged' diffs.
 */
function buildDiffs(base, decisions, which) {
    let tree = {};
    let sortedPaths = [];
    let local = which === 'local';
    let merged = which === 'merged';
    if (!local && !merged) {
        console.assert(which === 'remote');
    }
    for (let md of decisions) {
        let subdiffs = null;
        let spl = splitDiffStringPath(base, md.localPath);
        let path = spl[0];
        let line = spl[1];
        if (merged) {
            let sub = _resolvePathInObject(base, path);
            subdiffs = resolveAction(sub, md);
        }
        else {
            subdiffs = local ? md.localDiff : md.remoteDiff;
            if (subdiffs === null) {
                continue;
            }
        }
        let strPath = '/' + path.join('/');
        if (tree.hasOwnProperty(strPath)) {
            // Existing tree entry, simply add diffs to it
            if (line) {
                let matchDiff = util_1.getSubDiffByKey(tree[strPath].diff, line[0]);
                if (matchDiff) {
                    matchDiff.push.apply(matchDiff, subdiffs);
                }
                else {
                    subdiffs = pushPath(subdiffs, line);
                    tree[strPath].diff.push(subdiffs[0]);
                }
            }
            else {
                tree[strPath].diff = tree[strPath].diff.concat(subdiffs);
            }
        }
        else {
            // Make new entry in tree
            if (line) {
                subdiffs = pushPath(subdiffs, line);
            }
            tree[strPath] = { diff: subdiffs, path: path };
            sortedPaths.push(strPath);
        }
    }
    if (Object.keys(tree).length === 0) {
        return null;
    }
    if (!tree.hasOwnProperty('/')) {
        tree['/'] = { diff: [], path: [] };
        sortedPaths.push('/');
    }
    // Tree is constructed, now join all branches at diverging points (joints)
    return _mergeTree(tree, sortedPaths);
}
exports.buildDiffs = buildDiffs;
/**
 * Move a path prefix in a merge decision from `common_path` to the diffs.
 *
 * This is done by wrapping the diffs in nested patch ops.
 */
function pushPatchDecision(decision, prefix) {
    let dec = new MergeDecision(decision);
    // We need to start with inner most key to nest correctly, so reverse:
    for (let key of prefix.slice().reverse()) {
        if (dec.absolutePath.length === 0) {
            throw new Error('Cannot remove key from empty decision path: ' + key + ', ' + dec);
        }
        let popped = dec.absolutePath.pop();
        if (popped !== key) { // Pop and assert
            throw Error('Cannot push a patch that doesn\'t correspond to ' +
                'a key in the decision path! Key: ' + key +
                '; Remaining path: ' + dec.absolutePath.concat([popped]));
        }
        let ld = dec.localDiff && dec.localDiff.length > 0;
        let rd = dec.remoteDiff && dec.remoteDiff.length > 0;
        let cd = dec.customDiff && dec.customDiff.length > 0;
        dec.localDiff = ld ? [diffentries_1.opPatch(key, dec.localDiff)] : null;
        dec.remoteDiff = rd ? [diffentries_1.opPatch(key, dec.remoteDiff)] : null;
        dec.customDiff = cd ? [diffentries_1.opPatch(key, dec.customDiff)] : null;
    }
    return dec;
}
exports.pushPatchDecision = pushPatchDecision;
/**
 * Filter decisions based on matching (segment of) path
 *
 * Checks whether each decision's path start with `path`. If `skipLevels` is
 * given, the first levels of the decision's path is ignored for the comparison.
 *
 * Once matched, the matching decisions' levels are adjusted such that they
 * point to after the matching segment.
 *
 * Example:
 * Given a list of decisions with paths:
 *   /cells/0/outputs/0
 *   /cells/0/outputs/1
 *   /cells/2/outputs/1
 *   /cells/12/outputs/0/data
 *
 * If called with path `['cells']`:
 *   All decisions will be returned, with level set to 1
 * If called with path `['cells', 0]`:
 *   The first two will be returned, with level set to 2
 * If called with path `['outputs']`, and skipLevel = 2:
 *   All decisions will be returned, with level set to 3
 * If called with path `['outputs', 0]`, and skipLevel = 2:
 *   Decision 1 and 4 will be returned, with level set to 4
 *
 * Note that since the same decision instances are returned, this will modify
 * the level of the passed decisions.
 */
function filterDecisions(decisions, path, skipLevels, maxLength) {
    let ret = [];
    skipLevels = skipLevels || 0;
    for (let md of decisions) {
        if (maxLength !== undefined && md.absolutePath.length > maxLength) {
            continue;
        }
        if (util_2.isPrefixArray(path, md.absolutePath.slice(skipLevels))) {
            md.level = skipLevels + path.length;
            ret.push(md);
        }
    }
    return ret;
}
exports.filterDecisions = filterDecisions;
//# sourceMappingURL=decisions.js.map