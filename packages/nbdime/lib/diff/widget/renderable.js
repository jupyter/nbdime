// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
'use strict';
Object.defineProperty(exports, "__esModule", { value: true });
exports.RenderableDiffView = void 0;
const widgets_1 = require("@lumino/widgets");
/**
 * Widget for outputs with renderable MIME data.
 */
class RenderableDiffView extends widgets_1.Widget {
    constructor(model, editorClass, rendermime, mimetype) {
        super();
        this.rendermime = rendermime;
        this.model = model;
        this.mimetype = mimetype;
        let bdata = model.base;
        let rdata = model.remote;
        this.layout = new widgets_1.PanelLayout();
        let ci = 0;
        if (bdata) {
            let widget = this.createSubView(bdata, model.trusted);
            this.layout.addWidget(widget);
            widget.addClass(editorClass[ci++]);
        }
        if (rdata && rdata !== bdata) {
            let widget = this.createSubView(rdata, model.trusted);
            this.layout.addWidget(widget);
            widget.addClass(editorClass[ci++]);
        }
    }
}
exports.RenderableDiffView = RenderableDiffView;
//# sourceMappingURL=renderable.js.map