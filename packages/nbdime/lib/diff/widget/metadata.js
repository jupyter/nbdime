// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
'use strict';
Object.defineProperty(exports, "__esModule", { value: true });
exports.MetadataDiffWidget = void 0;
const widgets_1 = require("@lumino/widgets");
const mergeview_1 = require("../../common/mergeview");
const collapsiblepanel_1 = require("../../common/collapsiblepanel");
const common_1 = require("./common");
const ROOT_METADATA_CLASS = 'jp-Metadata-diff';
/**
 * MetadataWidget for changes to Notebook-level metadata
 */
class MetadataDiffWidget extends widgets_1.Panel {
    constructor(model) {
        super();
        this._model = model;
        console.assert(!model.added && !model.deleted);
        this.addClass(ROOT_METADATA_CLASS);
        this.init();
    }
    init() {
        let model = this._model;
        if (!model.unchanged) {
            this.addClass(common_1.TWOWAY_DIFF_CLASS);
            let view = mergeview_1.createNbdimeMergeView(model);
            if (model.collapsible) {
                view = new collapsiblepanel_1.CollapsiblePanel(view, model.collapsibleHeader, model.startCollapsed);
            }
            this.addWidget(view);
        }
    }
}
exports.MetadataDiffWidget = MetadataDiffWidget;
//# sourceMappingURL=metadata.js.map