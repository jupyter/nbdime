// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.

import type { CodeEditor } from '@jupyterlab/codeeditor';

import { type ITranslator, nullTranslator } from '@jupyterlab/translation';

import { Panel } from '@lumino/widgets';

import type {
  IDiffViewOptions,
  IDiffWidgetOptions,
  IMergeViewOptions,
} from './interfaces';

/**
 * Common panel for diff views
 */
export class DiffPanel<
  T,
  U extends IDiffViewOptions = IDiffViewOptions,
> extends Panel {
  constructor({
    model,
    editorFactory,
    translator,
    ...viewOptions
  }: IDiffWidgetOptions<T> & U) {
    super();
    this._editorFactory = editorFactory;
    this._model = model;
    this._translator = translator ?? nullTranslator;
    this._viewOptions = viewOptions as U;
  }

  protected _editorFactory: CodeEditor.Factory | undefined;
  protected _model: T;
  protected _translator: ITranslator;
  protected _viewOptions: U;
}

/**
 * Common panel for merge views
 */
export class MergePanel<T> extends DiffPanel<T, IMergeViewOptions> {}
