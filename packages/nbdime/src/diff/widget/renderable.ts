// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
'use strict';

import type { JSONValue, PartialJSONValue } from '@lumino/coreutils';

import { PanelLayout, Widget } from '@lumino/widgets';

import type { IRenderMimeRegistry } from '@jupyterlab/rendermime';

import type { RenderableDiffModel } from '../model';

/**
 * Widget for outputs with renderable MIME data.
 */
export abstract class RenderableDiffView<
  T extends JSONValue | PartialJSONValue,
> extends Widget {
  constructor(
    model: RenderableDiffModel<T>,
    editorClass: string[],
    rendermime: IRenderMimeRegistry,
    mimetype: string,
  ) {
    super();
    this.rendermime = rendermime;
    this.model = model;
    this.mimetype = mimetype;
    let bdata = model.base;
    let rdata = model.remote;
    this.layout = new PanelLayout();

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

  get layout(): PanelLayout | null {
    return super.layout as PanelLayout | null;
  }
  set layout(value: PanelLayout | null) {
    super.layout = value;
  }

  mimetype: string;

  /**
   * Create a widget which renders the given cell output
   */
  protected abstract createSubView(data: T, trusted: boolean): Widget;

  protected rendermime: IRenderMimeRegistry;

  protected model: RenderableDiffModel<T>;
}
