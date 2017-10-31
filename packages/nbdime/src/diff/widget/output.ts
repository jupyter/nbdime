// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
'use strict';

import {
  nbformat
} from '@jupyterlab/coreutils';

import {
  Widget
} from '@phosphor/widgets';

import {
  RenderMime, OutputModel
} from '@jupyterlab/rendermime';

import {
  RenderableDiffView
} from './renderable';

import {
  valueIn
} from '../../common/util';

import {
  OutputDiffModel
} from '../model';

import {
  stringify
} from '../../patch/stringified';


const RENDERED_OUTPUT_CLASS = 'jp-Diff-renderedOuput';

/**
 * Widget for outputs with renderable MIME data.
 */
export
class RenderableOutputView extends RenderableDiffView<nbformat.IOutput> {
  constructor(model: OutputDiffModel,
              editorClass: string[],
              rendermime: RenderMime) {
    super(model, editorClass, rendermime);
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
      if (nbformat.isExecuteResult(o) || nbformat.isDisplayData(o)) {
        let bundle = o.data;
        if (!RenderableDiffView.safeOrSanitizable(bundle)) {
          return false;
        }
      } else if (valueIn(o.output_type, ['stream', 'error'])) {
        // We "render" the text output, in terms of converting ANSI codes
        return true;
      }
    }
    return true;
  }

  protected createRawView(output: OutputModel): Widget {
    let widget = new Widget();
    widget.node.innerText = stringify(output.data);
    return widget;
  }

  /**
   * Create a widget which renders the given cell output
   */
  protected createSubView(output: nbformat.IOutput, trusted: boolean): Widget {
    let model = new OutputModel({value: output, trusted});
    let mimeType = this._rendermime.preferredMimeType(model.data, !trusted);
    if (!mimeType) {
      return this.createRawView(model);
    }
    let widget = this._rendermime.createRenderer(mimeType);
    widget.renderModel(model);
    widget.addClass(RENDERED_OUTPUT_CLASS);
    return widget;
  }

  _sanitized: boolean;
  _rendermime: RenderMime;
}
