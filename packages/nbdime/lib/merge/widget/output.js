// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
'use strict';
Object.defineProperty(exports, "__esModule", { value: true });
exports.RenderableOutputsMergeView = exports.ReorderableOutputWidget = exports.ReorderableOutputModel = void 0;
const outputarea_1 = require("@jupyterlab/outputarea");
const widgets_1 = require("@lumino/widgets");
const dragpanel_1 = require("../../common/dragpanel");
const flexpanel_1 = require("../../upstreaming/flexpanel");
const REORDERABLE_OUTPUT_CLASS = 'jp-Merge-reorder-outputs';
const REORDERABLE_OUTPUT_DRAGIMAGE_CLASS = 'jp-Merge-dragimage-output';
const DELETE_DROP_ZONE_CLASS = 'jp-Merge-output-drop-delete';
/**
 * An OutputAreaModel which allows for reordering of its
 * outputs.
 */
class ReorderableOutputModel extends outputarea_1.OutputAreaModel {
    insert(index, item) {
        // Note: We do not need worry about consolidating outputs
        // like the `add` method in parent class.
        this.list.insert(index, item);
    }
    move(fromIndex, toIndex) {
        // Note: We do not need worry about consolidating outputs
        // like the `add` method in parent class.
        this.list.move(fromIndex, toIndex);
    }
    remove(index) {
        return this.list.remove(index);
    }
}
exports.ReorderableOutputModel = ReorderableOutputModel;
/**
 * An OutputArea which supports the reordering
 * capabilities of ReorderableOutputModel
 */
class ReorderableOutputWidget extends outputarea_1.OutputArea {
    /**
     * Follow changes on the model state.
     */
    onModelChanged(sender, args) {
        let layout = this.layout;
        switch (args.type) {
            case 'move':
                layout.insertWidget(args.newIndex, layout.widgets[args.oldIndex]);
                break;
            case 'remove':
                layout.removeWidgetAt(args.oldIndex);
                break;
            default:
                return super.onModelChanged(sender, args);
        }
    }
}
exports.ReorderableOutputWidget = ReorderableOutputWidget;
class DisconnectedDropTarget extends dragpanel_1.DropPanel {
    constructor() {
        super({ acceptDropsFromExternalSource: true });
        this.callback = null;
    }
    findDropTarget(input) {
        if (input === this.node || this.node.contains(input)) {
            return this.node;
        }
        return null;
    }
    processDrop(dropTarget, event) {
        if (this.callback) {
            this.callback(dropTarget, event);
        }
    }
    ;
}
/**
 * Widget for showing side by side comparison and picking of merge outputs
 */
class RenderableOutputsMergeView extends dragpanel_1.DragDropPanel {
    /**
     *
     */
    constructor(merged, classes, rendermime, base, remote, local) {
        super();
        this.base = null;
        this.remote = null;
        this.local = null;
        this.addClass(REORDERABLE_OUTPUT_CLASS);
        if (!base !== !remote || !base !== !local) {
            // Assert that either none, or all of base/remote/local are given
            throw new Error('Renderable outputs merge-view either takes only merged output ' +
                'or a full set of four output lists.');
        }
        if (base) {
            this.base = new outputarea_1.OutputAreaModel();
            for (let output of base) {
                this.base.add(output);
            }
            this.remote = new outputarea_1.OutputAreaModel();
            for (let output of remote) {
                this.remote.add(output);
            }
            this.local = new outputarea_1.OutputAreaModel();
            for (let output of local) {
                this.local.add(output);
            }
        }
        this.merged = new ReorderableOutputModel();
        for (let output of merged) {
            this.merged.add(output);
        }
        this.rendermime = rendermime;
        this.panes = [];
        this.init(classes);
    }
    static makeOutputsDraggable(area) {
        let i = area.layout.iter();
        for (let w = i.next(); w !== undefined; w = i.next()) {
            dragpanel_1.DragPanel.makeHandle(w);
        }
    }
    static get deleteDrop() {
        if (!RenderableOutputsMergeView._deleteDrop) {
            let widget = new DisconnectedDropTarget();
            widget.addClass(DELETE_DROP_ZONE_CLASS);
            let icon = document.createElement('i');
            icon.className = 'fa fa-lg fa-trash-o';
            icon.setAttribute('aria-hidden', 'true');
            widget.node.appendChild(icon);
            widget.node.style.position = 'absolute';
            RenderableOutputsMergeView._deleteDrop = widget;
        }
        return RenderableOutputsMergeView._deleteDrop;
    }
    init(classes) {
        let row = new flexpanel_1.FlexPanel({ direction: 'left-to-right', evenSizes: true });
        if (this.local) {
            let leftPane = new outputarea_1.OutputArea({ model: this.local, rendermime: this.rendermime });
            leftPane.addClass(classes[1]);
            row.addWidget(leftPane);
            this.panes.push(leftPane);
        }
        if (this.base) {
            let basePane = new outputarea_1.OutputArea({ model: this.base, rendermime: this.rendermime });
            basePane.addClass(classes[0]);
            row.addWidget(basePane);
            this.panes.push(basePane);
        }
        if (this.remote) {
            let rightPane = new outputarea_1.OutputArea({ model: this.remote, rendermime: this.rendermime });
            rightPane.addClass(classes[2]);
            row.addWidget(rightPane);
            this.panes.push(rightPane);
        }
        if (row.widgets.length > 0) {
            this.addWidget(row);
            row = new flexpanel_1.FlexPanel({ direction: 'left-to-right', evenSizes: true });
        }
        this.mergePane = new ReorderableOutputWidget({ model: this.merged, rendermime: this.rendermime });
        this.mergePane.addClass(classes[3]);
        row.addWidget(this.mergePane);
        this.panes.push(this.mergePane);
        this.addWidget(row);
        for (let p of this.panes) {
            RenderableOutputsMergeView.makeOutputsDraggable(p);
        }
    }
    /**
     * Overrided version to allow drag and drop from source lists to merged list
     */
    findDragTarget(handle) {
        // First check for a drag handle
        if (handle === null) {
            return null;
        }
        // Next find out which pane it belongs to, and which output it belongs to
        for (let pane of this.panes) {
            let child = dragpanel_1.findChild(pane.node, handle);
            if (child !== null) {
                return child;
            }
        }
        return null;
    }
    getIndexOfChildNode(node, parent) {
        for (let pane of this.panes) {
            let child = dragpanel_1.findChild(pane.node, node);
            if (child !== null) {
                let paneIndex = this.panes.indexOf(pane);
                return [paneIndex, super.getIndexOfChildNode(child, pane.layout)];
            }
        }
        return null;
    }
    /**
     * Called when something has been dropped in the panel.
     *
     * As only internal moves are supported, we know the type of the keys
     */
    move(from, to) {
        let paneFrom = from[0];
        let paneTo = to[0];
        if (this.panes[paneTo] !== this.mergePane) {
            // Shouldn't happen if drop target code is correct...
            return;
        }
        let outputFrom = from[1];
        let outputTo = to[1];
        let adjustedTo = outputTo;
        if (paneFrom === paneTo) {
            if (outputTo > outputFrom) {
                // Have to adjust index for insertWidget in same instance
                adjustedTo -= 1;
                to[1] = adjustedTo;
            }
            else if (outputFrom === outputTo) {
                // No-op, same position
                return;
            }
        }
        let toModel = this.mergePane.model;
        let fromModel = this.panes[paneFrom].model;
        if (paneTo !== paneFrom) {
            toModel.insert(adjustedTo, fromModel.get(outputFrom));
        }
        else {
            toModel.move(outputFrom, adjustedTo);
        }
        RenderableOutputsMergeView.makeOutputsDraggable(this.mergePane);
    }
    /**
     * Find a drop target from a given node
     *
     * Returns null if no valid drop target was found.
     */
    findDropTarget(node) {
        if (node === this.mergePane.node && this.mergePane.model.length === 0) {
            // If empty, use pane as target
            return this.mergePane.node;
        }
        // Only valid drop target is in merge pane!
        return dragpanel_1.findChild(this.mergePane.node, node);
    }
    processDrop(dropTarget, event) {
        if (dropTarget === RenderableOutputsMergeView.deleteDrop.node) {
            // Simply remove output
            let [paneIdx, outputIdx] = event.mimeData.getData(dragpanel_1.MIME_INDEX);
            if (this.panes[paneIdx] !== this.mergePane) {
                // Shouldn't happen if drop target code is correct...
                return;
            }
            this.mergePane.model.remove(outputIdx);
            // Event cleanup
            event.preventDefault();
            event.stopPropagation();
            event.dropAction = 'move';
        }
        else if (dropTarget === this.mergePane.node && this.mergePane.model.length === 0) {
            // Dropping on empty merge pane
            let sourceKey = event.mimeData.getData(dragpanel_1.MIME_INDEX);
            this.move(sourceKey, [this.panes.indexOf(this.mergePane), 0]);
            // Event cleanup
            event.preventDefault();
            event.stopPropagation();
            event.dropAction = 'copy';
        }
        else {
            super.processDrop(dropTarget, event);
        }
    }
    getDragImage(handle) {
        let target = this.findDragTarget(handle);
        if (target) {
            let image = target.cloneNode(true);
            image.style.width = target.offsetWidth.toString() + 'px';
            image.classList.add(REORDERABLE_OUTPUT_DRAGIMAGE_CLASS);
            return image;
        }
        return null;
    }
    startDrag(handle, clientX, clientY) {
        super.startDrag(handle, clientX, clientY);
        // After starting drag, show delete drop-zone ('trash')
        if (dragpanel_1.findChild(this.mergePane.node, handle)) {
            let dd = RenderableOutputsMergeView.deleteDrop;
            dd.callback = this.processDrop.bind(this);
            // Calculate position and size:
            let ourRect = this.mergePane.node.getBoundingClientRect();
            dd.node.style.left = '0';
            dd.node.style.width = (ourRect.left + window.pageXOffset).toString() + 'px';
            dd.node.style.top = (ourRect.top + window.pageYOffset).toString() + 'px';
            dd.node.style.height = ourRect.height.toString() + 'px';
            // Attach to document
            widgets_1.Widget.attach(dd, document.body);
        }
    }
    onDragComplete(action) {
        super.onDragComplete(action);
        // After finishing drag, hide delete drop-zone ('trash')
        if (RenderableOutputsMergeView.deleteDrop.isAttached) {
            widgets_1.Widget.detach(RenderableOutputsMergeView.deleteDrop);
        }
    }
}
exports.RenderableOutputsMergeView = RenderableOutputsMergeView;
RenderableOutputsMergeView._deleteDrop = null;
//# sourceMappingURL=output.js.map