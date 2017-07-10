// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
'use strict';

import {
  nbformat
} from '@jupyterlab/coreutils';

import {
  JSONValue
} from '@phosphor/coreutils';

import {
  PanelLayout, Widget
} from '@phosphor/widgets';

import {
  RenderMime
} from '@jupyterlab/rendermime';

import {
  valueIn
} from '../../common/util';

import {
   RenderableDiffModel
} from '../model';



/**
 * A list of outputs considered safe.
 */
const safeOutputs = ['text/plain', 'text/latex', 'image/png', 'image/jpeg',
                    'application/vnd.jupyter.console-text'];

/**
 * A list of outputs that are sanitizable.
 */
const sanitizable = ['text/html'];

/**
 * Widget for outputs with renderable MIME data.
 */
export
abstract class RenderableDiffView<T extends JSONValue> extends Widget {
  constructor(model: RenderableDiffModel<T>, editorClass: string[],
              rendermime: RenderMime) {
    super();
    this._rendermime = rendermime;
    let bdata = model.base;
    let rdata = model.remote;
    this.layout = new PanelLayout();

    let ci = 0;
    if (bdata) {
      let widget = this.createSubView(bdata, false);
      this.layout.addWidget(widget);
      widget.addClass(editorClass[ci++]);
    }
    if (rdata && rdata !== bdata) {
      let widget = this.createSubView(rdata, false);
      this.layout.addWidget(widget);
      widget.addClass(editorClass[ci++]);
    }
  }

  /**
   * Checks if any MIME types of a MIME bundle are safe or can be sanitized.
   */
  static safeOrSanitizable(bundle: nbformat.IMimeBundle) {
    let keys = Object.keys(bundle);
    for (let key of keys) {
      if (valueIn(key, safeOutputs)) {
        return true;
      } else if (valueIn(key, sanitizable)) {
        let out = bundle[key];
        if (typeof out === 'string') {
          return true;
        }
      }
    }
    return false;
  }

  layout: PanelLayout;

  /**
   * Create a widget which renders the given cell output
   */
  protected abstract createSubView(data: T, trusted: boolean): Widget;

  _sanitized: boolean;
  _rendermime: RenderMime;
}
