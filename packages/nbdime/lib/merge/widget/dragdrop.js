// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
'use strict';
Object.defineProperty(exports, "__esModule", { value: true });
exports.ChunkedCellsWidget = exports.CellsDragDrop = void 0;
const widgets_1 = require("@lumino/widgets");
const signaling_1 = require("@lumino/signaling");
const dragpanel_1 = require("../../common/dragpanel");
const CELL_DRAG_DROP_CLASS = 'jp-merge-celldragdrop';
const MARK_CHUNK_RESOLVED_CLASS = 'jp-conflicted-cells-button';
const CHUNK_HEADER_CLASS = 'jp-conflicted-cells-header';
const CONLICTED_CELL_CHUNK_CLASS = 'jp-conflicted-cells';
class CellsDragDrop extends dragpanel_1.FriendlyDragDrop {
    /**
     *
     */
    constructor(options) {
        super(options);
        this._moved = new signaling_1.Signal(this);
        this.addClass(CELL_DRAG_DROP_CLASS);
    }
    /**
     * Called when something has been dropped in the panel.
     *
     * As only internal moves are supported, we know the type of the keys
     */
    move(from, to) {
        let friendFromId = from[0];
        let friendToId = to[0];
        let widgetFromId = from[1];
        let widgetToId = to[1];
        let adjustedTo = widgetToId;
        if (friendFromId === friendToId) {
            if (widgetToId > widgetFromId) {
                // Have to adjust index for insertWidget in same instance
                adjustedTo -= 1;
                to[1] = adjustedTo;
            }
            else if (widgetFromId === widgetToId) {
                // No-op, same position
                return;
            }
        }
        let toPanel = this.friends[friendToId];
        let fromPanel = this.friends[friendFromId];
        const cell = fromPanel.widgets[widgetFromId];
        toPanel.insertWidget(adjustedTo, cell);
        this._moved.emit({
            widget: cell,
            oldParent: fromPanel,
            before: adjustedTo > 0 ?
                toPanel.widgets[adjustedTo - 1] : null,
            after: adjustedTo < toPanel.widgets.length ?
                toPanel.widgets[adjustedTo + 1] : null,
        });
    }
    get moved() {
        return this._moved;
    }
}
exports.CellsDragDrop = CellsDragDrop;
class ChunkedCellsWidget extends widgets_1.Panel {
    /**
     *
     */
    constructor() {
        super();
        this._resolved = new signaling_1.Signal(this);
        this.addClass(CONLICTED_CELL_CHUNK_CLASS);
        this.header = new widgets_1.Widget();
        this.header.addClass(CHUNK_HEADER_CLASS);
        this.header.node.innerText = 'Conflicting cell operations';
        let button = document.createElement('button');
        button.innerText = 'Resolve Conflict';
        button.onclick = this.onResolve.bind(this);
        button.className = MARK_CHUNK_RESOLVED_CLASS;
        this.header.node.appendChild(button);
        this.addWidget(this.header);
        this.cells = new CellsDragDrop();
        this.addWidget(this.cells);
    }
    onResolve(event) {
        for (let cell of this.cells.widgets) {
            let model = cell.model;
            if (model.onesided && model.conflicted) {
                for (let d of model.decisions) {
                    d.conflict = false;
                }
            }
        }
        this.removeClass(CONLICTED_CELL_CHUNK_CLASS);
        this.header.parent = null;
        this.header.dispose();
        this._resolved.emit(undefined);
    }
    dispose() {
        this.cells.parent = null;
        this.cells = null;
        if (this.header) {
            this.header.parent = null;
        }
        this.header = null;
        super.dispose();
    }
    get resolved() {
        return this._resolved;
    }
}
exports.ChunkedCellsWidget = ChunkedCellsWidget;
//# sourceMappingURL=dragdrop.js.map