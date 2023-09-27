// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.

import { Panel } from "@lumino/widgets";
import type { IDiffWidgetOptions, IMergeWidgetOptions } from "./interfaces";
import type { CodeEditor } from "@jupyterlab/codeeditor";

/**
 * Common panel for diff views
 */
export class DiffPanel<T> extends Panel {
    constructor({
        model,
        editorFactory
      }: IDiffWidgetOptions<T>) {
        super();
        this._editorFactory = editorFactory;
        this._model = model;
      }

      protected _editorFactory: CodeEditor.Factory | undefined;
      protected _model: T;
}

/**
 * Common panel for merge views
 */
export class MergePanel<T> extends DiffPanel<T> {
    constructor({
        model,
        editorFactory,
        ...viewOptions
      }: IDiffWidgetOptions<T> & IMergeWidgetOptions) {
        super({model, editorFactory});
        this._viewOptions = viewOptions;
      }

      protected _viewOptions: IMergeWidgetOptions
}