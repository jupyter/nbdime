// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
'use strict';

import {
  Panel, Widget
} from '@lumino/widgets';

import { CodeEditor } from '@jupyterlab/codeeditor';

import {
  createNbdimeMergeView
} from '../../common/mergeview';

import {
  CollapsiblePanel
} from '../../common/collapsiblepanel';

import { IDiffWidgetOptions } from '../../common/interfaces';

import type {
  IStringDiffModel
} from '../model';

import {
  TWOWAY_DIFF_CLASS
} from './common';


const ROOT_METADATA_CLASS = 'jp-Metadata-diff';


/**
 * MetadataWidget for changes to Notebook-level metadata
 */
export
class MetadataDiffWidget extends Panel {
  // TODO improve typing hierarchy to avoid `Omit`
  constructor({model, editorFactory}: Omit<IDiffWidgetOptions<IStringDiffModel>, 'rendermime'>) {
    super();
    this._editorFactory = editorFactory;
    this._model = model;
    console.assert(!model.added && !model.deleted);
    this.addClass(ROOT_METADATA_CLASS);
    this.init();
  }

  init() {
    let model = this._model;
    if (!model.unchanged) {
      this.addClass(TWOWAY_DIFF_CLASS);
      let view: Widget = createNbdimeMergeView({remote: model, factory: this._editorFactory});
      if (model.collapsible) {
        view = new CollapsiblePanel(
          view, model.collapsibleHeader, model.startCollapsed);
      }
      this.addWidget(view);
    }
  }

  private _editorFactory: CodeEditor.Factory;
  private _model: IStringDiffModel;
}
