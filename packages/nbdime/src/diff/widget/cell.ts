// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
'use strict';

import { Panel, Widget } from '@lumino/widgets';

import type { CodeEditor } from '@jupyterlab/codeeditor';

import { IRenderMimeRegistry, MimeModel } from '@jupyterlab/rendermime';

import { DiffPanel } from '../../common/basepanel';

import { CollapsiblePanel } from '../../common/collapsiblepanel';

import type { ICellDiffWidgetOptions } from '../../common/interfaces';

import { createNbdimeMergeView } from '../../common/mergeview';

import { hasEntries } from '../../common/util';

import {
  CellDiffModel,
  IDiffModel,
  StringDiffModel,
  OutputDiffModel,
  ImmutableDiffModel,
} from '../model';

import {
  DIFF_CLASSES,
  ADDED_DIFF_CLASS,
  DELETED_DIFF_CLASS,
  TWOWAY_DIFF_CLASS,
  UNCHANGED_DIFF_CLASS,
  CHUNK_PANEL_CLASS,
  ADDED_CHUNK_PANEL_CLASS,
  REMOVED_CHUNK_PANEL_CLASS,
} from './common';

import { OutputPanel } from './output';

/**
 * The class name added to the prompt area of cell.
 */
const PROMPT_CLASS = 'jp-InputPrompt';

export const CELLDIFF_CLASS = 'jp-Cell-diff';

export const OUTPUTS_DIFF_CLASS = 'jp-Diff-outputsContainer';

const EXECUTIONCOUNT_ROW_CLASS = 'jp-Cellrow-executionCount';
const SOURCE_ROW_CLASS = 'jp-Cellrow-source';
const METADATA_ROW_CLASS = 'jp-Cellrow-metadata';
const OUTPUTS_ROW_CLASS = 'jp-Cellrow-outputs';

export interface ICellDiffViewOptions<T extends IDiffModel = IDiffModel> {
  model: T;
  parent: CellDiffModel;
  editorClasses: string[];
  rendermime: IRenderMimeRegistry;
  editorFactory?: CodeEditor.Factory;
}

/**
 * CellDiffWidget for cell changes
 */
export class CellDiffWidget extends DiffPanel<CellDiffModel> {
  /**
   *
   */
  constructor({
    rendermime,
    mimetype,
    ...others
  }: ICellDiffWidgetOptions<CellDiffModel>) {
    super(others);
    this.addClass(CELLDIFF_CLASS);
    this._rendermime = rendermime;
    this.mimetype = mimetype;

    this.init();
  }

  protected init() {
    let model = this.model;

    // Add 'cell added/deleted' notifiers, as appropriate
    let CURR_DIFF_CLASSES = DIFF_CLASSES.slice(); // copy
    if (model.added) {
      this.addClass(ADDED_DIFF_CLASS);
      CURR_DIFF_CLASSES = DIFF_CLASSES.slice(1, 2);
    } else if (model.deleted) {
      this.addClass(DELETED_DIFF_CLASS);
      CURR_DIFF_CLASSES = DIFF_CLASSES.slice(0, 1);
    } else if (model.unchanged) {
      this.addClass(UNCHANGED_DIFF_CLASS);
    } else {
      this.addClass(TWOWAY_DIFF_CLASS);
    }

    // Add inputs and outputs, on a row-by-row basis
    let sourceView = CellDiffWidget.createView({
      model: model.source,
      parent: model,
      editorClasses: CURR_DIFF_CLASSES,
      rendermime: this._rendermime,
      editorFactory: this._editorFactory,
    });
    sourceView.addClass(SOURCE_ROW_CLASS);
    if (model.executionCount) {
      sourceView.insertWidget(
        0,
        CellDiffWidget.createPrompts(model.executionCount, model),
      );
    }
    this.addWidget(sourceView);

    if (!model.metadata.unchanged) {
      let metadataView = CellDiffWidget.createView({
        model: model.metadata,
        parent: model,
        editorClasses: CURR_DIFF_CLASSES,
        rendermime: this._rendermime,
        editorFactory: this._editorFactory,
      });
      metadataView.addClass(METADATA_ROW_CLASS);
      this.addWidget(metadataView);
    }
    const chunks = model.getChunkedOutputs();
    if (hasEntries(chunks)) {
      let container = new Panel();
      container.addClass(OUTPUTS_DIFF_CLASS);
      let changed = false;
      for (let chunk of chunks) {
        if (chunk.length === 1) {
          let o = chunk[0];
          let outputsWidget = CellDiffWidget.createView({
            model: o,
            parent: model,
            editorClasses: CURR_DIFF_CLASSES,
            rendermime: this._rendermime,
            editorFactory: this._editorFactory,
          });
          container.addWidget(outputsWidget);
          changed = changed || !o.unchanged || o.added || o.deleted;
        } else {
          // Create add/remove chunk wrappers
          let chunkPanel = new Panel();
          chunkPanel.addClass(CHUNK_PANEL_CLASS);
          let addedPanel = new Panel();
          addedPanel.addClass(ADDED_CHUNK_PANEL_CLASS);
          let removedPanel = new Panel();
          removedPanel.addClass(REMOVED_CHUNK_PANEL_CLASS);
          for (let o of chunk) {
            let target = o.deleted ? removedPanel : addedPanel;
            let outputsWidget = CellDiffWidget.createView({
              model: o,
              parent: model,
              editorClasses: CURR_DIFF_CLASSES,
              rendermime: this._rendermime,
              editorFactory: this._editorFactory,
            });
            target.addWidget(outputsWidget);
            changed = changed || !o.unchanged || o.added || o.deleted;
          }
          chunkPanel.addWidget(addedPanel);
          chunkPanel.addWidget(removedPanel);
          container.addWidget(chunkPanel);
        }
      }
      if (model.added || model.deleted) {
        container.addClass(OUTPUTS_ROW_CLASS);
        this.addWidget(container);
      } else {
        let collapsed = !changed;
        let header = changed ? 'Outputs changed' : 'Outputs unchanged';
        let collapser = new CollapsiblePanel(container, header, collapsed);
        collapser.addClass(OUTPUTS_ROW_CLASS);
        this.addWidget(collapser);
      }
    }
  }

  static createPrompts(
    model: ImmutableDiffModel,
    parent: CellDiffModel,
  ): Panel {
    let prompts: string[] = [];
    if (!parent.added) {
      let base = model.base as number | null;
      let baseStr = `In [${base || ' '}]:`;
      prompts.push(baseStr);
    }
    if (!parent.unchanged && !parent.deleted) {
      let remote = model.remote as number | null;
      let remoteStr = `In [${remote || ' '}]:`;
      prompts.push(remoteStr);
    }
    const container = new Panel();
    container.addClass(`cm-merge-${prompts.length}pane`);
    for (let text of prompts) {
      let w = new Widget();
      w.node.innerText = text;
      w.addClass(PROMPT_CLASS);
      container.addWidget(w);
    }
    container.addClass(EXECUTIONCOUNT_ROW_CLASS);
    return container;
  }

  /**
   * Create a new sub-view.
   */
  static createView({
    model,
    parent,
    editorClasses,
    rendermime,
    editorFactory,
  }: ICellDiffViewOptions): Panel {
    let view: Panel;
    if (model instanceof StringDiffModel) {
      let inner: Widget | null = null;
      if (model.unchanged && parent.cellType === 'markdown') {
        let mimeModel = new MimeModel({
          data: { 'text/markdown': model.base! },
        });
        let mimeType = rendermime.preferredMimeType(mimeModel.data, 'ensure');
        if (!mimeType) {
          throw new Error('No renderer for output');
        }
        let renderer = rendermime.createRenderer(mimeType);
        renderer.renderModel(mimeModel);
        inner = renderer;
      } else {
        inner = createNbdimeMergeView({ remote: model, factory: editorFactory });
      }
      if (model.collapsible) {
        view = new CollapsiblePanel(
          inner,
          model.collapsibleHeader,
          model.startCollapsed,
        );
      } else {
        view = new Panel();
        view.addWidget(inner);
      }
    } else if (model instanceof OutputDiffModel) {
      view = new OutputPanel({
        model,
        parent,
        editorClasses,
        rendermime,
        editorFactory,
      });
      if (model.added) {
        view.addClass(ADDED_DIFF_CLASS);
      } else if (model.deleted) {
        view.addClass(DELETED_DIFF_CLASS);
      } else if (model.unchanged) {
        view.addClass(UNCHANGED_DIFF_CLASS);
      } else {
        view.addClass(TWOWAY_DIFF_CLASS);
      }
    } else {
      throw new Error('Unrecognized model type.');
    }
    return view;
  }

  mimetype: string;

  /**
   * Get the model for the widget.
   *
   * #### Notes
   * This is a read-only property.
   */
  get model(): CellDiffModel {
    return this._model;
  }

  protected _rendermime: IRenderMimeRegistry;
}
