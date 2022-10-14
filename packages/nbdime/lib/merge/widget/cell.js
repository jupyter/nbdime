// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
'use strict';
Object.defineProperty(exports, "__esModule", { value: true });
exports.CellMergeWidget = exports.CELLMERGE_CLASS = void 0;
const nbformat = require("@jupyterlab/nbformat");
const widgets_1 = require("@lumino/widgets");
const collapsiblepanel_1 = require("../../common/collapsiblepanel");
const dragpanel_1 = require("../../common/dragpanel");
const mergeview_1 = require("../../common/mergeview");
const util_1 = require("../../common/util");
const model_1 = require("../../diff/model");
const widget_1 = require("../../diff/widget");
const flexpanel_1 = require("../../upstreaming/flexpanel");
const output_1 = require("./output");
const common_1 = require("./common");
exports.CELLMERGE_CLASS = 'jp-Cell-merge';
const CELL_HEADER_CLASS = 'jp-Merge-cellHeader';
const CELL_HEADER_TITLE_CLASS = 'jp-Merge-cellHeader-title';
const MARKED_DELETE = 'jp-mod-todelete';
const MARKED_CLEAR_OUTPUTS = 'jp-mod-clearoutputs';
const CLEAR_OUTPUT_TOGGLE_CLASS = 'jp-Merge-clearOutput-toggle';
const DELETE_CELL_TOGGLE_CLASS = 'jp-Merge-delete-cell-toggle';
const EXECUTIONCOUNT_ROW_CLASS = 'jp-Cellrow-executionCount';
const SOURCE_ROW_CLASS = 'jp-Cellrow-source';
const METADATA_ROW_CLASS = 'jp-Cellrow-metadata';
const OUTPUTS_ROW_CLASS = 'jp-Cellrow-outputs';
const OUTPUTS_CONFLICTED_CLASS = 'jp-conflicted-outputs';
const MARK_OUTPUTS_RESOLVED_CLASS = 'jp-conflicted-outputs-button';
/**
 * CellMergeWidget for cell changes
 */
class CellMergeWidget extends widgets_1.Panel {
    /**
     *
     */
    constructor(model, rendermime, mimetype) {
        super();
        this.sourceView = null;
        this.metadataView = null;
        this.outputViews = null;
        this.addClass(exports.CELLMERGE_CLASS);
        this._model = model;
        this._rendermime = rendermime;
        this.mimetype = mimetype;
        this.init();
    }
    static createMergeView(local, remote, merged, editorClasses, readOnly = false) {
        let view = null;
        if (merged instanceof model_1.StringDiffModel) {
            view = mergeview_1.createNbdimeMergeView(remote, local, merged, readOnly);
        }
        return view;
    }
    static getOutputs(models, base) {
        let raw = [];
        for (let m of models) {
            if (base === true) {
                if (m.base) {
                    raw.push(m.base);
                }
            }
            else {
                if (m.remote) {
                    raw.push(m.remote);
                }
            }
        }
        return raw;
    }
    validateMerged(candidate) {
        if (this.sourceView && this.sourceView instanceof mergeview_1.MergeView) {
            let text = this.sourceView.getMergedValue();
            let lines = util_1.splitLines(text);
            if (candidate.source !== lines) {
                candidate.source = lines;
            }
        }
        if (this.metadataView && this.metadataView instanceof mergeview_1.MergeView) {
            let text = this.metadataView.getMergedValue();
            if (JSON.stringify(candidate.metadata) !== text) {
                // This will need to be validated server side,
                // and should not be touched by client side
                // (structure might differ from assumed form)
                candidate.metadata = JSON.parse(text);
            }
        }
        if (nbformat.isCode(candidate) && this.outputViews) {
            let model = this.outputViews.merged;
            let outputs = model.toJSON();
            candidate.outputs = outputs;
        }
        return candidate;
    }
    init() {
        let model = this.model;
        let CURR_CLASSES = common_1.MERGE_CLASSES.slice(); // copy
        this.createHeader();
        // Mark cells that have no changes:
        if (model.merged.unchanged &&
            model.local && model.local.unchanged &&
            model.remote && model.remote.unchanged) {
            this.addClass(common_1.UNCHANGED_MERGE_CLASS);
        }
        /*
         Two different display layouts depending on cell merge type:
         1. Unchanged or one way insert/delete of cell, or identical insert/delete:
            Single r/w editor (merged), with appropriate coloring for insert/delete
         2. Everything else:
            Full 4x merge view
        */
        let ladd = model.local && model.local.added;
        let ldel = model.local && model.local.deleted;
        let radd = model.remote && model.remote.added;
        let rdel = model.remote && model.remote.deleted;
        if (ladd && !radd || ldel && !rdel) {
            this.headerTitle = ladd ? 'Cell added locally' : 'Cell deleted locally';
        }
        else if (radd && !ladd || rdel && !ldel) {
            this.headerTitle = radd ? 'Cell added remotely' : 'Cell deleted remotely';
        }
        if (model.local === null || model.remote === null || ( // One sided change
        model.local.unchanged && model.remote.unchanged &&
            model.merged.unchanged) || // Unchanged
            model.local.added !== model.remote.added || // Onesided addition
            model.local.deleted && model.remote.unchanged || // Onesided deletion (other side unchanged)
            model.local.unchanged && model.remote.deleted || // Onesided deletion (other side unchanged)
            model.local.added && model.agreedCell || // Identical additions
            model.local.deleted && model.remote.deleted // Deletion on both
        ) {
            CURR_CLASSES = CURR_CLASSES.slice(1, 3);
            // Add single view of source:
            let view = widget_1.CellDiffWidget.createView(model.merged.source, model.merged, CURR_CLASSES, this._rendermime);
            if (ladd && !radd || ldel && !rdel) {
                this.addClass(common_1.ONEWAY_LOCAL_CLASS);
            }
            else if (radd && !ladd || rdel && !ldel) {
                this.addClass(common_1.ONEWAY_REMOTE_CLASS);
            }
            else if (ldel && rdel) {
                this.headerTitle = 'Deleted on both sides';
                this.addClass(common_1.TWOWAY_DELETION_CLASS);
            }
            else if (ladd && radd) {
                this.headerTitle = 'Added on both sides';
                this.addClass(common_1.TWOWAY_ADDITION_CLASS);
            }
            view.addClass(SOURCE_ROW_CLASS);
            this.addWidget(view);
            if (util_1.hasEntries(model.merged.outputs)) {
                // Add single view of rendered output
                let container = new widgets_1.Panel();
                for (let m of model.merged.outputs) {
                    view = widget_1.CellDiffWidget.createView(m, model.merged, CURR_CLASSES, this._rendermime);
                    container.addWidget(view);
                }
                container.addClass(OUTPUTS_ROW_CLASS);
                this.addWidget(container);
            }
        }
        else {
            // Setup full 4-way mergeview of source, metadata and outputs
            // as needed (if changed). Source/metadata/output are each a "row"
            let execDec = model.getExecutionCountDecision();
            if (execDec && execDec.action === 'clear') {
                let row = new flexpanel_1.FlexPanel({ direction: 'left-to-right' });
                row.addClass(EXECUTIONCOUNT_ROW_CLASS);
                let textWidget = new widgets_1.Widget();
                textWidget.node.innerText = 'Execution count will be cleared.';
                row.addWidget(textWidget);
                this.addWidget(row);
            }
            let sourceView = null;
            if (model.local && model.local.source.unchanged &&
                model.remote && model.remote.source.unchanged &&
                model.merged.source.unchanged) {
                // Use single unchanged view of source
                sourceView = widget_1.CellDiffWidget.createView(model.merged.source, model.merged, CURR_CLASSES, this._rendermime);
            }
            else {
                sourceView = CellMergeWidget.createMergeView(model.local ? model.local.source : null, model.remote ? model.remote.source : null, model.merged.source, CURR_CLASSES);
            }
            if (sourceView === null) {
                throw new Error('Was not able to create merge view for cell!');
            }
            this.sourceView = sourceView;
            sourceView.addClass(SOURCE_ROW_CLASS);
            this.addWidget(sourceView);
            let metadataChanged = false;
            let outputsChanged = false;
            for (let m of model.subModels) {
                if (!m || m.deleted) {
                    // Don't consider deleted cells
                    continue;
                }
                metadataChanged = metadataChanged || (!!m.metadata && !m.metadata.unchanged);
                if (m.outputs && m.outputs.length > 0) {
                    for (let o of m.outputs) {
                        outputsChanged = outputsChanged || !o.unchanged;
                    }
                }
            }
            if (metadataChanged) {
                let metadataView = CellMergeWidget.createMergeView(model.local ? model.local.metadata : null, model.remote ? model.remote.metadata : null, model.merged.metadata, CURR_CLASSES, true); // Do not allow manual edit of metadata
                if (metadataView === null) {
                    throw new Error('Was not able to create merge view for cell metadata!');
                }
                this.metadataView = metadataView;
                let container = new widgets_1.Panel();
                container.addWidget(metadataView);
                let header = 'Metadata changed';
                let collapser = new collapsiblepanel_1.CollapsiblePanel(container, header, true);
                collapser.addClass(METADATA_ROW_CLASS);
                this.addWidget(collapser);
            }
            if (outputsChanged || util_1.hasEntries(model.merged.outputs)) {
                // We know here that we have code cell
                // -> all have outputs !== null
                let baseOut = CellMergeWidget.getOutputs(model.local ? model.local.outputs : [], true);
                let localOut = CellMergeWidget.getOutputs(model.local ? model.local.outputs : []);
                let remoteOut = CellMergeWidget.getOutputs(model.remote ? model.remote.outputs : []);
                let mergedOut = CellMergeWidget.getOutputs(model.merged.outputs);
                let view = new output_1.RenderableOutputsMergeView(mergedOut, common_1.MERGE_CLASSES, this._rendermime, baseOut, remoteOut, localOut);
                this.outputViews = view;
                let header = outputsChanged ?
                    (model.outputsConflicted ?
                        'Outputs conflicted' :
                        'Outputs changed') :
                    'Outputs unchanged';
                let collapser = new collapsiblepanel_1.CollapsiblePanel(view, header, !outputsChanged);
                collapser.addClass(OUTPUTS_ROW_CLASS);
                if (model.outputsConflicted) {
                    collapser.addClass(OUTPUTS_CONFLICTED_CLASS);
                    let conflictClearBtn = new widgets_1.Widget();
                    conflictClearBtn.addClass(MARK_OUTPUTS_RESOLVED_CLASS);
                    let node = conflictClearBtn.node;
                    let btn = document.createElement('button');
                    btn.onclick = (ev) => {
                        if (ev.button !== 0) {
                            return; // Only main button clicks
                        }
                        model.clearOutputConflicts();
                        collapser.removeClass(OUTPUTS_CONFLICTED_CLASS);
                        collapser.headerTitle = 'Outputs changed';
                        ev.preventDefault();
                        ev.stopPropagation();
                        conflictClearBtn.parent = null;
                    };
                    btn.innerText = 'Mark resolved';
                    node.appendChild(btn);
                    collapser.header.insertWidget(1, conflictClearBtn);
                }
                this.addWidget(collapser);
            }
        }
    }
    createHeader() {
        let header = new widgets_1.Panel();
        header.addClass(CELL_HEADER_CLASS);
        // Add drag handle
        let w = dragpanel_1.DragPanel.createDefaultHandle();
        header.addWidget(w);
        // Add title widget
        w = new widgets_1.Widget();
        this.headerTitleWidget = w;
        w.addClass(CELL_HEADER_TITLE_CLASS);
        header.addWidget(w);
        if (util_1.hasEntries(this.model.merged.outputs)) {
            // Add "clear outputs" checkbox
            let clearOutputToggle = this._createClearOutputToggle();
            header.addWidget(clearOutputToggle);
        }
        // Add "delete cell" checkbox
        let deleteToggle = this._createDeleteToggle();
        header.addWidget(deleteToggle);
        // Add header to widget
        this.addWidget(header);
        this.header = header;
    }
    _createClearOutputToggle() {
        let { checkbox, widget } = common_1.createCheckbox(this.model.clearOutputs, 'Clear outputs');
        if (this.model.clearOutputs) {
            this.addClass(MARKED_CLEAR_OUTPUTS);
        }
        // Map checkbox -> model
        checkbox.onchange = (event) => {
            this.model.clearOutputs = checkbox.checked;
            this.toggleClass(MARKED_CLEAR_OUTPUTS, checkbox.checked);
        };
        // Map model -> checkbox
        this.model.clearOutputsChanged.connect((_model, value) => {
            checkbox.checked = value;
            this.toggleClass(MARKED_CLEAR_OUTPUTS, value);
        });
        widget.addClass(CLEAR_OUTPUT_TOGGLE_CLASS);
        return widget;
    }
    _createDeleteToggle() {
        let { checkbox, widget } = common_1.createCheckbox(this.model.deleteCell, 'Delete cell');
        if (this.model.deleteCell) {
            this.addClass(MARKED_DELETE);
        }
        // Map checkbox -> model
        checkbox.onchange = (event) => {
            this.model.deleteCell = checkbox.checked;
            this.toggleClass(MARKED_DELETE, checkbox.checked);
        };
        // Map model -> checkbox
        this.model.deleteCellChanged.connect((_model, value) => {
            checkbox.checked = value;
            this.toggleClass(MARKED_DELETE, value);
        });
        widget.addClass(DELETE_CELL_TOGGLE_CLASS);
        return widget;
    }
    set headerTitle(value) {
        this.headerTitleWidget.node.innerText = value;
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
exports.CellMergeWidget = CellMergeWidget;
//# sourceMappingURL=cell.js.map