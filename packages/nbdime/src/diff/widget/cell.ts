// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
'use strict';

import { Panel, Widget } from '@lumino/widgets';

import { IRenderMimeRegistry, MimeModel } from '@jupyterlab/rendermime';

import type { TranslationBundle } from '@jupyterlab/translation';

import { DiffPanel } from '../../common/basepanel';

import { CollapsiblePanel } from '../../common/collapsiblepanel';

import type {
  ICellDiffWidgetOptions,
  IMimeDiffWidgetOptions,
} from '../../common/interfaces';

import { createNbdimeMergeView } from '../../common/mergeview';

import { hasEntries } from '../../common/util';

import { FlexPanel } from '../../upstreaming/flexpanel';

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

const EXECUTION_COUNT_CLASS = 'jp-Cellrow-header-executionCount';
const CELL_ID_CLASS = 'jp-Cellrow-header-cellId';
const HEADER_ROW_CLASS = 'jp-Cellrow-header';
const SOURCE_ROW_CLASS = 'jp-Cellrow-source';
const METADATA_ROW_CLASS = 'jp-Cellrow-metadata';
const OUTPUTS_ROW_CLASS = 'jp-Cellrow-outputs';

export interface ICellDiffViewOptions<T extends IDiffModel = IDiffModel>
  extends IMimeDiffWidgetOptions<T> {
  parent: CellDiffModel;
  editorClasses: string[];
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
    this._trans = this._translator.load('nbdime');
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
      translator: this._translator,
      ...this._viewOptions,
    });
    sourceView.addClass(SOURCE_ROW_CLASS);

    if (model.executionCount || model.cellId) {
      const createWidget = (text: string): Widget => {
        let w = new Widget();
        w.node.innerText = text;
        return w;
      };
      const header = CellDiffWidget.createHeader();
      FlexPanel.setGrow(header, 1);
      sourceView.insertWidget(0, header);

      const prompts = model.executionCount
        ? CellDiffWidget.createPrompts(model.executionCount, model)
        : { base: null, remote: null };
      const ids = model.cellId
        ? CellDiffWidget.createIdentifiers(model.cellId, model)
        : { base: null, remote: null };

      const views: ('base' | 'remote')[] = ['base', 'remote'];
      for (let side of views) {
        const prompt = prompts[side];
        const id = ids[side];
        if (model.executionCount && prompt !== null) {
          let w = createWidget(prompt);
          w.addClass(PROMPT_CLASS);
          w.addClass(EXECUTION_COUNT_CLASS);
          header.addWidget(w);
        }
        if (model.cellId && id !== null) {
          let w = createWidget(`Cell ID: ${id}`);
          w.addClass(CELL_ID_CLASS);
          FlexPanel.setGrow(w, 1);
          header.addWidget(w);
        }
      }
    }

    this.addWidget(sourceView);

    if (!model.metadata.unchanged) {
      let metadataView = CellDiffWidget.createView({
        model: model.metadata,
        parent: model,
        editorClasses: CURR_DIFF_CLASSES,
        rendermime: this._rendermime,
        editorFactory: this._editorFactory,
        translator: this._translator,
        ...this._viewOptions,
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
            translator: this._translator,
            ...this._viewOptions,
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
              translator: this._translator,
              ...this._viewOptions,
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
        let header = changed
          ? this._trans.__('Outputs changed')
          : this._trans.__('Outputs unchanged');
        let collapser = new CollapsiblePanel(container, header, collapsed);
        collapser.addClass(OUTPUTS_ROW_CLASS);
        this.addWidget(collapser);
      }
    }
  }

  static createHeader(): Panel {
    let container = new FlexPanel({ direction: 'left-to-right' });
    container.addClass(HEADER_ROW_CLASS);
    return container;
  }

  static createPrompts(
    model: ImmutableDiffModel,
    parent: CellDiffModel,
  ): Record<'base' | 'remote', string | null> {
    const prompts: Record<'base' | 'remote', string | null> = {
      base: null,
      remote: null,
    };
    if (!parent.added) {
      let base = model.base as number | null;
      prompts.base = `In [${base || ' '}]:`;
    }
    if (!parent.unchanged && !parent.deleted) {
      let remote = model.remote as number | null;
      prompts.remote = `In [${remote || ' '}]:`;
    }
    return prompts;
  }

  static createIdentifiers(
    model: ImmutableDiffModel,
    parent: CellDiffModel,
  ): Record<'base' | 'remote', string | null> {
    return {
      base: model.base as string | null,
      remote: model.remote as string | null,
    };
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
    translator,
    ...viewOptions
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
        inner = createNbdimeMergeView({
          remote: model,
          factory: editorFactory,
          translator,
          ...viewOptions,
        });
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
        translator,
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
  protected _trans: TranslationBundle;
}
