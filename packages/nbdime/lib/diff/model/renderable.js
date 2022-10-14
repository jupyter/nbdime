// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
'use strict';
Object.defineProperty(exports, "__esModule", { value: true });
exports.RenderableDiffModel = void 0;
const coreutils_1 = require("@lumino/coreutils");
const signaling_1 = require("@lumino/signaling");
const util_1 = require("../util");
const patch_1 = require("../../patch");
const string_1 = require("./string");
/**
 * Diff model for a renderable object (something that has an internal MimeBundle)
 *
 * Can be converted to a StringDiffModel via the method `stringify()`, which also
 * takes an optional argument `key` which specifies a subpath of the IOutput to
 * make the model from.
 */
class RenderableDiffModel {
    constructor(base, remote, diff) {
        this.trustedChanged = new signaling_1.Signal(this);
        if (!remote && !base) {
            throw new Error('Either remote or base value need to be given');
        }
        this.base = base;
        if (!remote && diff) {
            this.remote = patch_1.patch(base, diff);
        }
        else {
            this.remote = remote;
        }
        this.diff = diff || null;
        this.collapsible = false;
    }
    get unchanged() {
        return JSON.stringify(this.base) === JSON.stringify(this.remote);
    }
    get added() {
        return this.base === null;
    }
    get deleted() {
        return this.remote === null;
    }
    /**
     * Convert to a StringDiffModel.
     *
     * Takes an optional argument `key` which specifies a subpath of the MimeBundle to
     * make the model from.
     */
    stringify(key) {
        let getMemberByPath = function (obj, key, f) {
            if (!obj) {
                return obj;
            }
            if (Array.isArray(key)) {
                const tail = key.length > 2 ? key.slice(1) : key[1];
                if (f) {
                    return getMemberByPath(f(obj, key[0]), tail, f);
                }
                return getMemberByPath(obj[key[0]], tail, f);
            }
            else if (f) {
                return f(obj, key);
            }
            return obj[key];
        };
        const baseCopy = coreutils_1.JSONExt.deepCopy(this.base);
        let base = key ? getMemberByPath(baseCopy, key) : baseCopy;
        const remoteCopy = coreutils_1.JSONExt.deepCopy(this.remote);
        let remote = key ? getMemberByPath(remoteCopy, key) : remoteCopy;
        let diff = (this.diff && key) ?
            getMemberByPath(this.diff, key, util_1.getSubDiffByKey) :
            this.diff;
        let model = null;
        if (this.unchanged || this.added || this.deleted || !diff) {
            model = string_1.createDirectStringDiffModel(base, remote);
        }
        else {
            model = string_1.createPatchStringDiffModel(base, diff);
        }
        model.mimetype = key ? this.innerMimeType(key) : 'application/json';
        model.collapsible = this.collapsible;
        model.collapsibleHeader = this.collapsibleHeader;
        model.startCollapsed = this.startCollapsed;
        return model;
    }
    /**
     * Whether outputs are trusted
     */
    get trusted() {
        return this._trusted;
    }
    set trusted(value) {
        if (this._trusted !== value) {
            this._trusted = value;
            this.trustedChanged.emit(value);
        }
    }
    /**
     * The present values of model.base/remote
     */
    get contents() {
        let ret = [];
        if (this.base) {
            ret.push(this.base);
        }
        if (this.remote && this.remote !== this.base) {
            ret.push(this.remote);
        }
        return ret;
    }
}
exports.RenderableDiffModel = RenderableDiffModel;
//# sourceMappingURL=renderable.js.map