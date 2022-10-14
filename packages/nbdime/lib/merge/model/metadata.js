// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
'use strict';
Object.defineProperty(exports, "__esModule", { value: true });
exports.MetadataMergeModel = void 0;
const model_1 = require("../../diff/model");
const common_1 = require("./common");
const coreutils_1 = require("@lumino/coreutils");
/**
 * Model of a merge of metadata with decisions
 */
class MetadataMergeModel extends common_1.ObjectMergeModel {
    constructor(base, decisions) {
        super(base, decisions, 'application/json');
    }
    serialize() {
        if (!this.merged || this.merged.remote === null) {
            throw new Error('Missing notebook metadata merge data.');
        }
        // This will check whether metadata is valid JSON.
        // Validation of compatibility vs notebook format
        // will happen on server side.
        return JSON.parse(this.merged.remote);
    }
    createDiffModel(diff) {
        if (diff && diff.length > 0) {
            return model_1.createPatchStringDiffModel(this.base, diff);
        }
        else {
            const baseCopy = coreutils_1.JSONExt.deepCopy(this.base);
            return model_1.createDirectStringDiffModel(baseCopy, baseCopy);
        }
    }
    createMergedDiffModel() {
        return new common_1.DecisionStringDiffModel(this.base, this.decisions, [this.local, this.remote]);
    }
}
exports.MetadataMergeModel = MetadataMergeModel;
//# sourceMappingURL=metadata.js.map