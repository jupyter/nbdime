// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
'use strict';

import {
  nbformat
} from '@jupyterlab/coreutils';

import {
  RenderMime, IOutputModel
} from '@jupyterlab/rendermime';

import {
  OutputArea, OutputAreaModel, IOutputAreaModel
} from '@jupyterlab/outputarea';

import {
  IObservableList
} from '@jupyterlab/coreutils/lib/observablelist';

import {
  DropAction, IDragEvent
} from '@phosphor/dragdrop';

import {
  PanelLayout, Widget
} from '@phosphor/widgets';

import {
  DragDropPanel, DropPanel, DragPanel, findChild, MIME_INDEX
} from '../../common/dragpanel';

import {
  FlexPanel
} from '../../upstreaming/flexpanel';


const REORDERABLE_OUTPUT_CLASS = 'jp-Merge-reorder-outputs';
const REORDERABLE_OUTPUT_DRAGIMAGE_CLASS = 'jp-Merge-dragimage-output';
const DELETE_DROP_ZONE_CLASS = 'jp-Merge-output-drop-delete';


/**
 * An OutputAreaModel which allows for reordering of its
 * outputs.
 */
export
class ReorderableOutputModel extends OutputAreaModel {

  insert(index: number, item: IOutputModel): void {
    // Note: We do not need worry about consolidating outputs
    // like the `add` method in parent class.
    this.list.insert(index, item);
  }

  move(fromIndex: number, toIndex: number): void {
    // Note: We do not need worry about consolidating outputs
    // like the `add` method in parent class.
    this.list.move(fromIndex, toIndex);
  }

  remove(index: number): IOutputModel | undefined {
    return this.list.remove(index);
  }
}

/**
 * An OutputArea which supports the reordering
 * capabilities of ReorderableOutputModel
 */
export
class ReorderableOutputWidget extends OutputArea {

  readonly model: ReorderableOutputModel;

  /**
   * Follow changes on the model state.
   */
  protected onModelChanged(sender: IOutputAreaModel, args: IObservableList.IChangedArgs<IOutputModel>) {
    let layout = this.layout as PanelLayout;
    switch (args.type) {
    case 'move':
      layout.insertWidget(args.newIndex,
        layout.widgets[args.oldIndex]);
      break;
    case 'remove':
      layout.removeWidgetAt(args.oldIndex);
      break;
    default:
      return super.onModelChanged(sender, args);
    }
  }
}


class DisconnectedDropTarget extends DropPanel {
  constructor() {
    super({acceptDropsFromExternalSource: true});
  }

  protected findDropTarget(input: HTMLElement): HTMLElement | null  {
    if (input === this.node || this.node.contains(input)) {
      return this.node;
    }
    return null;
  }

  protected processDrop(dropTarget: HTMLElement, event: IDragEvent): void {
    if (this.callback) {
      this.callback(dropTarget, event);
    }
  };

  callback: ((dropTarget: HTMLElement, event: IDragEvent) => void) | null = null;
}


/**
 * Widget for showing side by side comparison and picking of merge outputs
 */
export
class RenderableOutputsMergeView extends DragDropPanel {

  static makeOutputsDraggable(area: OutputArea): void {
    let i = area.layout!.iter();
    for (let w = i.next(); w !== undefined; w = i.next()) {
      DragPanel.makeHandle(w);
    }
  }

  private static get deleteDrop(): DisconnectedDropTarget {
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
  private static _deleteDrop: DisconnectedDropTarget | null = null;

  /**
   *
   */
  constructor(merged: nbformat.IOutput[],
              classes: string[], rendermime: RenderMime,
              base: nbformat.IOutput[] | null, remote: nbformat.IOutput[] | null,
              local: nbformat.IOutput[] | null) {
    super();
    this.addClass(REORDERABLE_OUTPUT_CLASS);

    if (!base !== !remote || !base !== !local) {
      // Assert that either none, or all of base/remote/local are given
      throw new Error(
        'Renderable outputs merge-view either takes only merged output ' +
        'or a full set of four output lists.');
    }

    if (base) {
      this.base = new OutputAreaModel();
      for (let output of base) {
          this.base.add(output);
      }
      this.remote = new OutputAreaModel();
      for (let output of remote!) {
          this.remote.add(output);
      }
      this.local = new OutputAreaModel();
      for (let output of local!) {
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

  init(classes: string[]): void {
    let row = new FlexPanel({direction: 'left-to-right', evenSizes: true});
    if (this.local) {
      let leftPane = new OutputArea({model: this.local, rendermime: this.rendermime});
      leftPane.addClass(classes[1]);
      row.addWidget(leftPane);
      this.panes.push(leftPane);
    }
    if (this.base) {
      let basePane = new OutputArea({model: this.base, rendermime: this.rendermime});
      basePane.addClass(classes[0]);
      row.addWidget(basePane);
      this.panes.push(basePane);
    }
    if (this.remote) {
      let rightPane = new OutputArea({model: this.remote, rendermime: this.rendermime});
      rightPane.addClass(classes[2]);
      row.addWidget(rightPane);
      this.panes.push(rightPane);
    }
    if (row.widgets.length > 0) {
      this.addWidget(row);
      row = new FlexPanel({direction: 'left-to-right', evenSizes: true});
    }

    this.mergePane = new ReorderableOutputWidget({model: this.merged, rendermime: this.rendermime});
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
  protected findDragTarget(handle: HTMLElement): HTMLElement | null {
    // First check for a drag handle
    if (handle === null) {
      return null;
    }

    // Next find out which pane it belongs to, and which output it belongs to
    for (let pane of this.panes) {
      let child = findChild(pane.node, handle);
      if (child !== null) {
        return child;
      }
    }
    return null;
  }

  /**
   * Overrided version to allow identifying source pane and source output
   */
  protected targetFromKey(key: any): Widget {
    let indices = key as number[];
    let paneIndex = indices[0];
    let outputIndex = indices[1];
    let pane = this.panes[paneIndex];
    return (pane.layout as PanelLayout).widgets[outputIndex];
  }

  protected getIndexOfChildNode(node: HTMLElement, parent?: PanelLayout): any {
    for (let pane of this.panes) {
      let child = findChild(pane.node, node);
      if (child !== null) {
        let paneIndex = this.panes.indexOf(pane);
        return [paneIndex, super.getIndexOfChildNode(child,
                pane.layout as PanelLayout)];
      }
    }
    return null;
  }


  /**
   * Called when something has been dropped in the panel.
   *
   * As only internal moves are supported, we know the type of the keys
   */
  protected move(from: number[], to: number[]): void {
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
      } else if (outputFrom === outputTo) {
        // No-op, same position
        return;
      }
    }
    let toModel = this.mergePane.model;
    let fromModel = this.panes[paneFrom].model;
    if (paneTo !== paneFrom) {
      toModel.insert(adjustedTo, fromModel.get(outputFrom));
    } else {
      toModel.move(outputFrom, adjustedTo);
    }
    RenderableOutputsMergeView.makeOutputsDraggable(this.mergePane);
  }

  /**
   * Find a drop target from a given node
   *
   * Returns null if no valid drop target was found.
   */
  protected findDropTarget(node: HTMLElement): HTMLElement | null {
    if (node === this.mergePane.node && this.mergePane.model.length === 0) {
      // If empty, use pane as target
      return this.mergePane.node;
    }
    // Only valid drop target is in merge pane!
    return findChild(this.mergePane.node, node);
  }

  protected processDrop(dropTarget: HTMLElement, event: IDragEvent): void {
    if (dropTarget === RenderableOutputsMergeView.deleteDrop.node) {
      // Simply remove output
      let [paneIdx, outputIdx] = event.mimeData.getData(MIME_INDEX) as number[];
      if (this.panes[paneIdx] !== this.mergePane) {
        // Shouldn't happen if drop target code is correct...
        return;
      }
      this.mergePane.model.remove(outputIdx);
      // Event cleanup
      event.preventDefault();
      event.stopPropagation();
      event.dropAction = 'move';
    } else if (dropTarget === this.mergePane.node && this.mergePane.model.length === 0) {
      // Dropping on empty merge pane
      let sourceKey = event.mimeData.getData(MIME_INDEX) as number[];
      this.move(sourceKey, [this.panes.indexOf(this.mergePane), 0]);
      // Event cleanup
      event.preventDefault();
      event.stopPropagation();
      event.dropAction = 'copy';
    } else {
      super.processDrop(dropTarget, event);
    }
  }

  protected getDragImage(handle: HTMLElement) {
    let target = this.findDragTarget(handle);
    if (target) {
      let image = target.cloneNode(true) as HTMLElement;
      image.style.width = target.offsetWidth.toString() + 'px';
      image.classList.add(REORDERABLE_OUTPUT_DRAGIMAGE_CLASS);
      return image;
    }
    return null;
  }

  protected startDrag(handle: HTMLElement, clientX: number, clientY: number): void {
    super.startDrag(handle, clientX, clientY);
    // After starting drag, show delete drop-zone ('trash')
    if (findChild(this.mergePane.node, handle)) {
      let dd = RenderableOutputsMergeView.deleteDrop;
      dd.callback = this.processDrop.bind(this);
      // Calculate position and size:
      let ourRect = this.mergePane.node.getBoundingClientRect();
      dd.node.style.left = '0';
      dd.node.style.width = (ourRect.left + window.pageXOffset).toString() + 'px';
      dd.node.style.top = (ourRect.top + window.pageYOffset).toString() + 'px';
      dd.node.style.height = ourRect.height.toString() + 'px';
      // Attach to document
      Widget.attach(dd, document.body);
    }
  }

  protected onDragComplete(action: DropAction) {
    super.onDragComplete(action);
    // After finishing drag, hide delete drop-zone ('trash')
    if (RenderableOutputsMergeView.deleteDrop.isAttached) {
      Widget.detach(RenderableOutputsMergeView.deleteDrop);
    }
  }

  base: OutputAreaModel | null = null;

  remote: OutputAreaModel | null = null;

  local: OutputAreaModel | null = null;

  merged: ReorderableOutputModel;

  mergePane: ReorderableOutputWidget;

  panes: OutputArea[];

  rendermime: RenderMime;
}
