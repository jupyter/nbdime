// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
'use strict';

import {
  IRenderMime
} from 'jupyterlab/lib/rendermime';

import {
  OutputWidget
} from 'jupyterlab/lib/notebook/output-area';

import {
  nbformat
} from 'jupyterlab/lib/notebook/notebook/nbformat';

import {
  Widget
} from 'phosphor/lib/ui/widget';

import {
  PanelLayout
} from 'phosphor/lib/ui/panel';

import {
  valueIn
} from '../../common/util';

import {
   OutputDiffModel
} from '../model';


const RENDERED_OUTPUT_CLASS = 'jp-Diff-renderedOuput';

/**
 * A list of outputs considered safe.
 */
const safeOutputs = ['text/plain', 'text/latex', 'image/png', 'image/jpeg',
                    'application/vnd.jupyter.console-text'];

/**
 * A list of outputs that are sanitizable.
 */
const sanitizable = ['text/svg', 'text/html'];

/**
 * Widget for outputs with renderable MIME data.
 */
export
class RenderableOutputView extends Widget {
  constructor(model: OutputDiffModel, editorClass: string[],
              rendermime: IRenderMime) {
    super();
    this._rendermime = rendermime;
    let bdata = model.base;
    let rdata = model.remote;
    this.layout = new PanelLayout();
    this.addClass(RENDERED_OUTPUT_CLASS);

    let ci = 0;
    if (bdata) {
      let widget = this.createOutput(bdata, false);
      this.layout.addWidget(widget);
      widget.addClass(editorClass[ci++]);
    }
    if (rdata && rdata !== bdata) {
      let widget = this.createOutput(rdata, false);
      this.layout.addWidget(widget);
      widget.addClass(editorClass[ci++]);
    }
  }

  /**
   * Checks if all MIME types of a MIME bundle are safe or can be sanitized.
   */
  static safeOrSanitizable(bundle: nbformat.MimeBundle) {
    let keys = Object.keys(bundle);
    for (let key of keys) {
      if (valueIn(key, safeOutputs)) {
        continue;
      } else if (valueIn(key, sanitizable)) {
        let out = bundle[key];
        if (typeof out === 'string') {
          continue;
        } else {
          return false;
        }
      } else {
        return false;
      }
    }
    return true;
  }

  /**
   * Checks if a cell output can be rendered as untrusted (either safe or
   * sanitizable)
   */
  static canRenderUntrusted(model: OutputDiffModel): boolean {
    let toTest: nbformat.IOutput[] = [];
    if (model.base) {
      toTest.push(model.base);
    }
    if (model.remote && model.remote !== model.base) {
      toTest.push(model.remote);
    }
    for (let o of toTest) {
      if (o.output_type === 'execute_result' || o.output_type === 'display_data') {
        let bundle = o.data;
        if (!this.safeOrSanitizable(bundle)) {
          return false;
        }
      } else if (valueIn(o.output_type, ['stream', 'error'])) {
        // Unknown output type
        return false;
      }
    }
    return true;
  }

  layout: PanelLayout;

  /**
   * Create a widget which renders the given cell output
   */
  protected createOutput(output: nbformat.IOutput, trusted: boolean): Widget {
    let widget = new OutputWidget({rendermime: this._rendermime});
    widget.render({output, trusted});
    return widget;
  }

  _sanitized: boolean;
  _rendermime: IRenderMime;
}