// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
'use strict';
Object.defineProperty(exports, "__esModule", { value: true });
exports.createImmutableModel = exports.ImmutableDiffModel = void 0;
/**
 * Standard implementation of the IStringDiffModel interface.
 */
class ImmutableDiffModel {
    /**
     * ImmutableDiffModel constructor.
     *
     * `collapsible` and `collapsed` both defaults to false.
     */
    constructor(base, remote, collapsible, header, collapsed) {
        this.base = base;
        this.remote = remote;
        this.collapsible = collapsible === true;
        if (this.collapsible) {
            this.collapsibleHeader = header ? header : '';
            this.startCollapsed = collapsed === true;
        }
    }
    get unchanged() {
        return this.base === this.remote;
    }
    get added() {
        return this.base === undefined;
    }
    get deleted() {
        return this.remote === undefined;
    }
}
exports.ImmutableDiffModel = ImmutableDiffModel;
/**
 * Create an ImmutableDiffModel from a base value, a remote value, and a single diff entry.
 *
 * Note: The requirement of a single diff entry means it will not support
 * an add/replace pair on the same key, as this should instead be represented
 * by a 'replace' op.
 *
 * @export
 * @param {(ImmutableValue | undefined)} base : The base value
 * @param {(IDiffImmutableObjectEntry | null)} diff : The diff entry, or null if unchanged
 * @returns {ImmutableDiffModel}
 */
function createImmutableModel(base, remote, diff) {
    if (!diff) {
        return new ImmutableDiffModel(base, remote);
    }
    else if (diff.op === 'add') {
        if (base !== undefined) {
            throw new Error('Invalid diff op on immutable value');
        }
        return new ImmutableDiffModel(base, diff.value);
    }
    else if (diff.op === 'remove') {
        if (base === undefined) {
            throw new Error('Invalid diff op on immutable value');
        }
        return new ImmutableDiffModel(base, undefined);
    }
    else { // diff.op === 'replace'
        if (base === undefined) {
            throw new Error('Invalid diff op on immutable value');
        }
        return new ImmutableDiffModel(base, diff.value);
    }
}
exports.createImmutableModel = createImmutableModel;
//# sourceMappingURL=immutable.js.map