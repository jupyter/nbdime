// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
'use strict';
Object.defineProperty(exports, "__esModule", { value: true });
exports.NotebookMergeWidget = void 0;
const widgets_1 = require("@lumino/widgets");
const util_1 = require("../../common/util");
const flexpanel_1 = require("../../upstreaming/flexpanel");
const metadata_1 = require("./metadata");
const cell_1 = require("./cell");
const common_1 = require("./common");
const dragdrop_1 = require("./dragdrop");
const NBMERGE_CLASS = 'jp-Notebook-merge';
const NB_MERGE_CONTROLS_CLASS = 'jp-Merge-notebook-controls';
/**
 * NotebookMergeWidget
 */
class NotebookMergeWidget extends widgets_1.Panel {
    constructor(model, rendermime) {
        super();
        this.metadataWidget = null;
        this._model = model;
        this._rendermime = rendermime;
        this.addClass(NBMERGE_CLASS);
    }
    /**
     * Start adding sub-widgets.
     *
     * Separated from constructor to allow 'live' adding of widgets
     */
    init() {
        let model = this._model;
        let rendermime = this._rendermime;
        let work = Promise.resolve();
        this.addWidget(new NotebookMergeControls(model));
        work = work.then(() => {
            if (model.metadata) {
                this.metadataWidget = new metadata_1.MetadataMergeWidget(model.metadata);
                this.addWidget(this.metadataWidget);
            }
        });
        work = work.then(() => {
            this.cellContainer = new dragdrop_1.CellsDragDrop({ acceptDropsFromExternalSource: true });
            this.cellContainer.setFriendlyGroup(dragdrop_1.CellsDragDrop.makeGroup());
            this.cellContainer.moved.connect(this.onDragDropMove, this);
            this.addWidget(this.cellContainer);
        });
        this.cellWidgets = [];
        let chunk = null;
        for (let c of model.cells) {
            work = work.then(() => {
                return new Promise((resolve) => {
                    let w = new cell_1.CellMergeWidget(c, rendermime, model.mimetype);
                    this.cellWidgets.push(w);
                    if (c.onesided && c.conflicted) {
                        if (chunk === null) {
                            chunk = new dragdrop_1.ChunkedCellsWidget();
                            chunk.cells.moved.connect(this.onDragDropMove, this);
                            chunk.resolved.connect(this.onChunkResolved, this);
                            this.cellContainer.addToFriendlyGroup(chunk.cells);
                        }
                        chunk.cells.addWidget(w);
                    }
                    else {
                        if (chunk !== null) {
                            this.cellContainer.addWidget(chunk);
                            chunk = null;
                        }
                        this.cellContainer.addWidget(w);
                    }
                    // This limits us to drawing 60 cells per second, which shouldn't
                    // be a problem...
                    requestAnimationFrame(() => {
                        resolve();
                    });
                });
            });
        }
        work = work.then(() => {
            if (chunk !== null) {
                this.cellContainer.addWidget(chunk);
            }
        });
        return work;
    }
    validateMerged(candidate) {
        let validated = util_1.deepCopy(candidate);
        // Validate metadata
        if (this.metadataWidget) {
            validated.metadata = this.metadataWidget.validateMerged(candidate.metadata);
        }
        // Validate cells
        let i = 0;
        for (let c of this.cellWidgets) {
            if (!c.model.deleteCell) {
                validated.cells[i] = c.validateMerged(candidate.cells[i]);
                ++i;
            }
        }
        return validated;
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
    onDragDropMove(sender, args) {
        // Move cell in model list
        let { widget, oldParent, before, after } = args;
        let from = this._model.cells.indexOf(widget.model);
        let to;
        if (after) {
            to = this._model.cells.indexOf(after.model);
        }
        else if (before) {
            to = this._model.cells.indexOf(before.model) + 1;
        }
        else {
            throw new Error('Need either before or after');
        }
        if (to > from) {
            to -= 1;
        }
        this._model.cells.splice(to, 0, this._model.cells.splice(from, 1)[0]);
        if (oldParent.widgets.length === 0) {
            let chunk = oldParent.parent;
            chunk.onResolve();
        }
        // Mark any conflict on a cell moved from chunk as resolved
        if (oldParent !== this.cellContainer && widget.parent === this.cellContainer) {
            for (let d of widget.model.decisions) {
                d.conflict = false;
            }
        }
    }
    onChunkResolved(sender, args) {
        let index = this.cellContainer.widgets.indexOf(sender);
        while (sender.cells.widgets.length > 0) {
            this.cellContainer.insertWidget(index++, sender.cells.widgets[0]);
        }
        sender.parent = null;
        sender.dispose();
    }
}
exports.NotebookMergeWidget = NotebookMergeWidget;
/**
 * Collection of notebook-wide controls
 */
class NotebookMergeControls extends flexpanel_1.FlexPanel {
    constructor(model) {
        super({
            direction: 'left-to-right'
        });
        this.model = model;
        this.addClass(NB_MERGE_CONTROLS_CLASS);
        let anyOutputs = false;
        for (let cell of model.cells) {
            if (util_1.hasEntries(cell.merged.outputs)) {
                anyOutputs = true;
                break;
            }
        }
        if (anyOutputs) {
            this.init_controls();
        }
    }
    init_controls() {
        // Add "Clear all outputs" checkbox
        let chk = common_1.createCheckbox(false, 'Clear <i>all</i> cell outputs');
        this.clearOutputsToggle = chk.checkbox;
        this.addWidget(chk.widget);
        // Add "Clear all conflicted outputs" checkbox
        chk = common_1.createCheckbox(false, 'Clear <i>conflicted</i> cell outputs');
        this.clearConflictedOutputsToggle = chk.checkbox;
        this.addWidget(chk.widget);
        this.updateOutputsToggles();
        this.connectOutputsToggles();
    }
    connectOutputsToggles() {
        for (let cell of this.model.cells) {
            if (util_1.hasEntries(cell.merged.outputs)) {
                cell.clearOutputsChanged.connect(this.updateOutputsToggles, this);
            }
        }
        this.clearOutputsToggle.addEventListener('change', this);
        this.clearConflictedOutputsToggle.addEventListener('change', this);
    }
    disconnectOutputsToggles() {
        for (let cell of this.model.cells) {
            if (util_1.hasEntries(cell.merged.outputs)) {
                cell.clearOutputsChanged.disconnect(this.updateOutputsToggles, this);
            }
        }
        this.clearOutputsToggle.removeEventListener('change', this);
        this.clearConflictedOutputsToggle.removeEventListener('change', this);
    }
    handleEvent(event) {
        switch (event.type) {
            case 'change':
                if (event.currentTarget === this.clearOutputsToggle) {
                    this.onClearAllOutputsChanged();
                }
                else if (event.currentTarget === this.clearConflictedOutputsToggle) {
                    this.onClearConflictedOutputsChanged();
                }
                break;
            default:
                break;
        }
    }
    onClearAllOutputsChanged() {
        this.disconnectOutputsToggles();
        try {
            let value = this.clearOutputsToggle.checked;
            for (let cell of this.model.cells) {
                if (util_1.hasEntries(cell.merged.outputs)) {
                    cell.clearOutputs = value;
                }
            }
        }
        finally {
            this.updateOutputsToggles();
            this.connectOutputsToggles();
        }
    }
    onClearConflictedOutputsChanged() {
        this.disconnectOutputsToggles();
        try {
            let value = this.clearConflictedOutputsToggle.checked;
            for (let cell of this.model.cells) {
                if (util_1.hasEntries(cell.merged.outputs) && cell.outputsConflicted) {
                    cell.clearOutputs = value;
                }
            }
        }
        finally {
            this.updateOutputsToggles();
            this.connectOutputsToggles();
        }
    }
    updateOutputsToggles() {
        // null = indeterminate
        let all = undefined;
        let conflicted = undefined;
        for (let cell of this.model.cells) {
            if (util_1.hasEntries(cell.merged.outputs)) {
                let current = cell.clearOutputs;
                if (all === null) {
                    // Indeterminate, current value won't change it
                }
                else if (all === undefined) {
                    all = current;
                }
                else if (all !== current) {
                    all = null;
                }
                if (cell.outputsConflicted) {
                    if (conflicted === null) {
                        // Indeterminate, current value won't change it
                    }
                    else if (conflicted === undefined) {
                        conflicted = current;
                    }
                    else if (conflicted !== current) {
                        conflicted = null;
                    }
                }
            }
            if (conflicted === null && all === null) {
                // Both indeterminate, short circuit
                break;
            }
        }
        this.clearOutputsToggle.checked = all === true;
        this.clearOutputsToggle.indeterminate = all === null;
        this.clearConflictedOutputsToggle.checked = conflicted === true;
        this.clearConflictedOutputsToggle.indeterminate = conflicted === null;
        this.clearConflictedOutputsToggle.disabled = conflicted === undefined;
        if (conflicted === undefined) {
            this.clearConflictedOutputsToggle.parentElement.setAttribute('disabled', '');
        }
        else {
            this.clearConflictedOutputsToggle.parentElement.removeAttribute('disabled');
        }
    }
}
//# sourceMappingURL=notebook.js.map