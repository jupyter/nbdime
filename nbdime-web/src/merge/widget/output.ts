// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
'use strict';

import {
  IRenderMime
} from 'jupyterlab/lib/rendermime';

import {
  OutputAreaWidget, OutputAreaModel
} from 'jupyterlab/lib/notebook/output-area';

import {
  IListChangedArgs
} from 'jupyterlab/lib/common/observablelist';

import {
  nbformat
} from 'jupyterlab/lib/notebook/notebook/nbformat';

import {
  DragDropPanel, DragPanel, findChild
} from '../../common/dragpanel';

import {
  Widget
} from 'phosphor/lib/ui/widget';

import {
  PanelLayout
} from 'phosphor/lib/ui/panel';

import {
  FlexPanel
} from '../../upstreaming/flexpanel';



/**
 * An OutputAreaModel which allows for reordering of its
 * outputs.
 */
export
class ReorderableOutputModel extends OutputAreaModel {

  insert(index: number, item: OutputAreaModel.Output): void {
    // Note: We do not need worry about consolidating outputs
    // like the `add` method in parent class.
    this.list.insert(index, item);
  }

  move(fromIndex: number, toIndex: number): void {
    // Note: We do not need worry about consolidating outputs
    // like the `add` method in parent class.
    this.list.move(fromIndex, toIndex);
  }
}

/**
 * An OutputAreaWidget which supports the reordering
 * capabilities of ReorderableOutputModel
 */
export
class ReorderableOutputWidget extends OutputAreaWidget {

  model: ReorderableOutputModel;

  protected onModelStateChanged(sender: OutputAreaModel, args: IListChangedArgs<nbformat.IOutput>) {
    switch (args.type) {
    case 'add':
      // Children are NOT always added at the end.
      this.addChild(args.newIndex);
      break;
    case 'move':
      let layout = this.layout as PanelLayout;
      layout.insertWidget(args.newIndex,
        layout.widgets.at(args.oldIndex));
      break;
    default:
      return super.onModelStateChanged(sender, args);
    }
  }

  protected addChild(index?: number): void {
    super.addChild();
    let layout = this.layout as PanelLayout;
    if (index !== undefined && index !== layout.widgets.length - 1) {
      // Move the widget added at the end
      layout.insertWidget(index,
        layout.widgets.at(layout.widgets.length - 1));
      // Update new widget to match the newly inserted
      // model item
      this.updateChild(index);
    }
  }
}

/**
 * Widget for showing side by side comparison and picking of merge outputs
 */
export
class RenderableOutputsMergeView extends DragDropPanel {

  static makeOutputsDraggable(area: OutputAreaWidget): void {
    let i = area.layout.iter();
    for (let w = i.next(); w !== undefined; w = i.next()) {
      DragPanel.makeHandle(w);
    }
  }

  /**
   *
   */
  constructor(merged: nbformat.IOutput[],
              classes: string[], rendermime: IRenderMime,
              base: nbformat.IOutput[] | null, remote: nbformat.IOutput[] | null,
              local: nbformat.IOutput[] | null) {
    super();

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
      let leftPane = new OutputAreaWidget({rendermime: this.rendermime});
      leftPane.addClass(classes[1]);
      leftPane.model = this.local;
      row.addWidget(leftPane);
      this.panes.push(leftPane);
    }
    if (this.base) {
      let basePane = new OutputAreaWidget({rendermime: this.rendermime});
      basePane.addClass(classes[0]);
      basePane.model = this.base;
      row.addWidget(basePane);
      this.panes.push(basePane);
    }
    if (this.remote) {
      let rightPane = new OutputAreaWidget({rendermime: this.rendermime});
      rightPane.addClass(classes[2]);
      rightPane.model = this.remote;
      row.addWidget(rightPane);
      this.panes.push(rightPane);
    }
    if (row.widgets.length > 0) {
      this.addWidget(row);
      row = new FlexPanel({direction: 'left-to-right', evenSizes: true});
    }
    this.mergePane = new ReorderableOutputWidget({rendermime: this.rendermime});
    this.mergePane.addClass(classes[3]);
    this.mergePane.model = this.merged;
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
    return (pane.layout as PanelLayout).widgets.at(outputIndex);
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
    // Only valid drop target is in merge pane!
    return findChild(this.mergePane.node, node);
  }

  protected getDragImage(handle: HTMLElement) {
    let target = this.findDragTarget(handle);
    if (target) {
      let image = target.cloneNode(true) as HTMLElement;
      image.style.width = target.offsetWidth.toString() + 'px';
      return image;
    }
    return null;
  }

  base: OutputAreaModel | null = null;

  remote: OutputAreaModel | null = null;

  local: OutputAreaModel | null = null;

  merged: ReorderableOutputModel;

  mergePane: ReorderableOutputWidget;

  panes: OutputAreaWidget[];

  rendermime: IRenderMime;
}
