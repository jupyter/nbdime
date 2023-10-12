// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
'use strict';

import { nullTranslator, type ITranslator } from '@jupyterlab/translation';

import { Panel, Widget } from '@lumino/widgets';

import { Signal, ISignal } from '@lumino/signaling';

import { FriendlyDragDrop, DragDropPanel } from '../../common/dragpanel';

import type { CellMergeWidget } from './cell';

const CELL_DRAG_DROP_CLASS = 'jp-merge-celldragdrop';

const MARK_CHUNK_RESOLVED_CLASS = 'jp-conflicted-cells-button';
const CHUNK_HEADER_CLASS = 'jp-conflicted-cells-header';
const CONFLICTED_CELL_CHUNK_CLASS = 'jp-conflicted-cells';

export class CellsDragDrop extends FriendlyDragDrop {
  /**
   *
   */
  constructor(options?: DragDropPanel.IOptions) {
    super(options);
    this.addClass(CELL_DRAG_DROP_CLASS);
  }

  /**
   * Called when something has been dropped in the panel.
   *
   * As only internal moves are supported, we know the type of the keys
   */
  protected move(from: number[], to: number[]): void {
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
      } else if (widgetFromId === widgetToId) {
        // No-op, same position
        return;
      }
    }
    let toPanel = this.friends[friendToId];
    let fromPanel = this.friends[friendFromId];
    const cell = fromPanel.widgets[widgetFromId];
    toPanel.insertWidget(adjustedTo, cell);
    this._moved.emit({
      widget: cell as CellMergeWidget,
      oldParent: fromPanel as CellsDragDrop,
      before:
        adjustedTo > 0
          ? (toPanel.widgets[adjustedTo - 1] as CellMergeWidget)
          : null,
      after:
        adjustedTo < toPanel.widgets.length
          ? (toPanel.widgets[adjustedTo + 1] as CellMergeWidget)
          : null,
    });
  }

  get moved(): ISignal<this, CellsDragDrop.IMovedArgs> {
    return this._moved;
  }

  private _moved = new Signal<this, CellsDragDrop.IMovedArgs>(this);
}

export namespace CellsDragDrop {
  export interface IMovedArgs {
    widget: CellMergeWidget;
    oldParent: CellsDragDrop;
    before: CellMergeWidget | null;
    after: CellMergeWidget | null;
  }
}

export class ChunkedCellsWidget extends Panel {
  /**
   *
   */
  constructor({ translator }: { translator?: ITranslator } = {}) {
    super();
    const trans = (translator ?? nullTranslator).load('nbdime');
    this.addClass(CONFLICTED_CELL_CHUNK_CLASS);
    this.header = new Widget();
    this.header.addClass(CHUNK_HEADER_CLASS);
    this.header.node.textContent = trans.__('Conflicting cell operations');
    let button = document.createElement('button');
    button.textContent = trans.__('Resolve Conflict');
    button.onclick = this.onResolve.bind(this);
    button.className = MARK_CHUNK_RESOLVED_CLASS;
    this.header.node.appendChild(button);
    this.addWidget(this.header);
    this.cells = new CellsDragDrop();
    this.addWidget(this.cells);
  }

  onResolve(event?: MouseEvent) {
    for (let cell of this.cells.widgets) {
      let model = (cell as CellMergeWidget).model;
      if (model.onesided && model.conflicted) {
        for (let d of model.decisions) {
          d.conflict = false;
        }
      }
    }
    this.removeClass(CONFLICTED_CELL_CHUNK_CLASS);
    this.header.parent = null;
    this.header.dispose();
    this._resolved.emit(undefined);
  }

  dispose() {
    this.cells.parent = null;
    this.cells = null!;
    if (this.header) {
      this.header.parent = null;
    }
    this.header = null!;
    super.dispose();
  }

  header: Widget;

  cells: CellsDragDrop;

  get resolved(): ISignal<this, void> {
    return this._resolved;
  }

  private _resolved = new Signal<this, void>(this);
}
