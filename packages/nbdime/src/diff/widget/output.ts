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
  IRenderMimeRegistry, OutputModel
} from '@jupyterlab/rendermime';

import {
  RenderableDiffView
} from './renderable';

import {
  valueIn, intersection
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
              rendermime: IRenderMimeRegistry) {
    super(model, editorClass, rendermime);
  }

  /**
   * Whether trust can affect the output rendering.
   */
  static isTrustSignificant(model: OutputDiffModel, rendermime: RenderMime): boolean {
    let toTest: nbformat.IOutput[] = [];
    if (model.base) {
      toTest.push(model.base);
    }
    if (model.remote && model.remote !== model.base) {
      toTest.push(model.remote);
    }
    for (let o of toTest) {
      let untrustedModel = new OutputModel({value: o, trusted: model.trusted});
      let modelMimeTypes = untrustedModel.data.keys();
      let rendererMimeTypes = toArray(rendermime.mimeTypes());
      let candidates = intersection(modelMimeTypes, rendererMimeTypes);
      for (let mimeType of candidates) {
        let renderer = rendermime.getRenderer(mimeType);
        let options = {mimeType, model: untrustedModel, sanitizer: rendermime.sanitizer}
        if (!renderer.canRender(options) || renderer.wouldSanitize(options)) {
          return true;
        }
      }
    }
    return false;
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
  _rendermime: IRenderMimeRegistry;
}
