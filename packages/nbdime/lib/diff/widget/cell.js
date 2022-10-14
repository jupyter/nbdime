// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
'use strict';
Object.defineProperty(exports, "__esModule", { value: true });
exports.CellDiffWidget = exports.OUTPUTS_DIFF_CLASS = exports.CELLDIFF_CLASS = void 0;
const widgets_1 = require("@lumino/widgets");
const rendermime_1 = require("@jupyterlab/rendermime");
const flexpanel_1 = require("../../upstreaming/flexpanel");
const collapsiblepanel_1 = require("../../common/collapsiblepanel");
const mergeview_1 = require("../../common/mergeview");
const util_1 = require("../../common/util");
const model_1 = require("../model");
const common_1 = require("./common");
const output_1 = require("./output");
/**
 * The class name added to the prompt area of cell.
 */
const PROMPT_CLASS = 'jp-InputPrompt';
exports.CELLDIFF_CLASS = 'jp-Cell-diff';
exports.OUTPUTS_DIFF_CLASS = 'jp-Diff-outputsContainer';
const EXECUTIONCOUNT_ROW_CLASS = 'jp-Cellrow-executionCount';
const SOURCE_ROW_CLASS = 'jp-Cellrow-source';
const METADATA_ROW_CLASS = 'jp-Cellrow-metadata';
const OUTPUTS_ROW_CLASS = 'jp-Cellrow-outputs';
/**
 * CellDiffWidget for cell changes
 */
class CellDiffWidget extends widgets_1.Panel {
    /**
     *
     */
    constructor(model, rendermime, mimetype) {
        super();
        this.addClass(exports.CELLDIFF_CLASS);
        this._model = model;
        this._rendermime = rendermime;
        this.mimetype = mimetype;
        this.init();
    }
    init() {
        let model = this.model;
        // Add 'cell added/deleted' notifiers, as appropriate
        let CURR_DIFF_CLASSES = common_1.DIFF_CLASSES.slice(); // copy
        if (model.added) {
            this.addClass(common_1.ADDED_DIFF_CLASS);
            CURR_DIFF_CLASSES = common_1.DIFF_CLASSES.slice(1, 2);
        }
        else if (model.deleted) {
            this.addClass(common_1.DELETED_DIFF_CLASS);
            CURR_DIFF_CLASSES = common_1.DIFF_CLASSES.slice(0, 1);
        }
        else if (model.unchanged) {
            this.addClass(common_1.UNCHANGED_DIFF_CLASS);
        }
        else {
            this.addClass(common_1.TWOWAY_DIFF_CLASS);
        }
        // Add inputs and outputs, on a row-by-row basis
        let sourceView = CellDiffWidget.createView(model.source, model, CURR_DIFF_CLASSES, this._rendermime);
        sourceView.addClass(SOURCE_ROW_CLASS);
        if (model.executionCount) {
            sourceView.insertWidget(0, CellDiffWidget.createPrompts(model.executionCount, model));
        }
        this.addWidget(sourceView);
        if (!model.metadata.unchanged) {
            let metadataView = CellDiffWidget.createView(model.metadata, model, CURR_DIFF_CLASSES, this._rendermime);
            metadataView.addClass(METADATA_ROW_CLASS);
            this.addWidget(metadataView);
        }
        const chunks = model.getChunkedOutputs();
        if (util_1.hasEntries(chunks)) {
            let container = new widgets_1.Panel();
            container.addClass(exports.OUTPUTS_DIFF_CLASS);
            let changed = false;
            for (let chunk of chunks) {
                if (chunk.length === 1) {
                    let o = chunk[0];
                    let outputsWidget = CellDiffWidget.createView(o, model, CURR_DIFF_CLASSES, this._rendermime);
                    container.addWidget(outputsWidget);
                    changed = changed || !o.unchanged || o.added || o.deleted;
                }
                else {
                    // Create add/remove chunk wrappers
                    let chunkPanel = new widgets_1.Panel();
                    chunkPanel.addClass(common_1.CHUNK_PANEL_CLASS);
                    let addedPanel = new widgets_1.Panel();
                    addedPanel.addClass(common_1.ADDED_CHUNK_PANEL_CLASS);
                    let removedPanel = new widgets_1.Panel();
                    removedPanel.addClass(common_1.REMOVED_CHUNK_PANEL_CLASS);
                    for (let o of chunk) {
                        let target = o.deleted ? removedPanel : addedPanel;
                        let outputsWidget = CellDiffWidget.createView(o, model, CURR_DIFF_CLASSES, this._rendermime);
                        target.addWidget(outputsWidget);
                        changed = changed || !o.unchanged || o.added || o.deleted;
                    }
                    chunkPanel.addWidget(addedPanel);
                    chunkPanel.addWidget(removedPanel);
                    container.addWidget(chunkPanel);
                }
            }
            if (model.added || model.deleted) {
                container.addClass(OUTPUTS_ROW_CLASS);
                this.addWidget(container);
            }
            else {
                let collapsed = !changed;
                let header = changed ? 'Outputs changed' : 'Outputs unchanged';
                let collapser = new collapsiblepanel_1.CollapsiblePanel(container, header, collapsed);
                collapser.addClass(OUTPUTS_ROW_CLASS);
                this.addWidget(collapser);
            }
        }
    }
    static createPrompts(model, parent) {
        let prompts = [];
        if (!parent.added) {
            let base = model.base;
            let baseStr = `In [${base || ' '}]:`;
            prompts.push(baseStr);
        }
        if (!parent.unchanged && !parent.deleted) {
            let remote = model.remote;
            let remoteStr = `In [${remote || ' '}]:`;
            prompts.push(remoteStr);
        }
        let container = new flexpanel_1.FlexPanel({ direction: 'left-to-right' });
        for (let text of prompts) {
            let w = new widgets_1.Widget();
            w.node.innerText = text;
            w.addClass(PROMPT_CLASS);
            container.addWidget(w);
            flexpanel_1.FlexPanel.setGrow(w, 1);
        }
        container.addClass(EXECUTIONCOUNT_ROW_CLASS);
        return container;
    }
    /**
     * Create a new sub-view.
     */
    static createView(model, parent, editorClasses, rendermime) {
        let view;
        if (model instanceof model_1.StringDiffModel) {
            let inner = null;
            if (model.unchanged && parent.cellType === 'markdown') {
                let mimeModel = new rendermime_1.MimeModel({ data: { 'text/markdown': model.base } });
                let mimeType = rendermime.preferredMimeType(mimeModel.data, 'ensure');
                if (!mimeType) {
                    throw new Error('No renderer for output');
                }
                let renderer = rendermime.createRenderer(mimeType);
                renderer.renderModel(mimeModel);
                inner = renderer;
            }
            else {
                inner = mergeview_1.createNbdimeMergeView(model);
            }
            if (model.collapsible) {
                view = new collapsiblepanel_1.CollapsiblePanel(inner, model.collapsibleHeader, model.startCollapsed);
            }
            else {
                view = new widgets_1.Panel();
                view.addWidget(inner);
            }
        }
        else if (model instanceof model_1.OutputDiffModel) {
            view = new output_1.OutputPanel(model, parent, editorClasses, rendermime);
            if (model.added) {
                view.addClass(common_1.ADDED_DIFF_CLASS);
            }
            else if (model.deleted) {
                view.addClass(common_1.DELETED_DIFF_CLASS);
            }
            else if (model.unchanged) {
                view.addClass(common_1.UNCHANGED_DIFF_CLASS);
            }
            else {
                view.addClass(common_1.TWOWAY_DIFF_CLASS);
            }
        }
        else {
            throw new Error('Unrecognized model type.');
        }
        return view;
    }
    /**
     * Get the model for the widget.
     *
     * #### Notes
     * This is a read-only property.
     */
    get model() {
        return this._model;
    }
}
exports.CellDiffWidget = CellDiffWidget;
//# sourceMappingURL=cell.js.map