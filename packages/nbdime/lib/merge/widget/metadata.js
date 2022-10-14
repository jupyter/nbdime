// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
'use strict';
Object.defineProperty(exports, "__esModule", { value: true });
exports.MetadataMergeWidget = void 0;
const widgets_1 = require("@lumino/widgets");
const mergeview_1 = require("../../common/mergeview");
const collapsiblepanel_1 = require("../../common/collapsiblepanel");
const ROOT_METADATA_CLASS = 'jp-Metadata-diff';
/**
 * MetadataWidget for changes to Notebook-level metadata
 */
class MetadataMergeWidget extends widgets_1.Panel {
    constructor(model) {
        super();
        this._model = model;
        this.addClass(ROOT_METADATA_CLASS);
        this.init();
    }
    init() {
        let model = this._model;
        // We know/assume that MetadataMergeModel never has
        // null values for local/remote:
        this.view = mergeview_1.createNbdimeMergeView(model.remote, model.local, model.merged);
        let wrapper = new collapsiblepanel_1.CollapsiblePanel(this.view, 'Notebook metadata changed', true);
        this.addWidget(wrapper);
    }
    validateMerged(candidate) {
        let text = this.view.getMergedValue();
        if (JSON.stringify(candidate) !== text) {
            // This will need to be validated server side,
            // and should not be touched by client side
            // (structure might differ from assumed form)
            candidate = JSON.parse(text);
        }
        return candidate;
    }
}
exports.MetadataMergeWidget = MetadataMergeWidget;
//# sourceMappingURL=metadata.js.map