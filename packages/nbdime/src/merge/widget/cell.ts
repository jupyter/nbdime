// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
'use strict';

import * as nbformat from '@jupyterlab/nbformat';

import { Panel, Widget } from '@lumino/widgets';

import type { CodeEditor } from '@jupyterlab/codeeditor';

import type { IRenderMimeRegistry } from '@jupyterlab/rendermime';

import type { TranslationBundle } from '@jupyterlab/translation';

import { MergePanel } from '../../common/basepanel';

import { CollapsiblePanel } from '../../common/collapsiblepanel';

import { DragPanel } from '../../common/dragpanel';

import type {
  ICellDiffWidgetOptions,
  IMergeViewOptions,
} from '../../common/interfaces';

import { createNbdimeMergeView, MergeView } from '../../common/mergeview';

import { hasEntries, splitLines } from '../../common/util';

import {
  IStringDiffModel,
  StringDiffModel,
  IDiffModel,
  OutputDiffModel,
} from '../../diff/model';

import { CellDiffWidget } from '../../diff/widget';

import { FlexPanel } from '../../upstreaming/flexpanel';

import type { CellMergeModel } from '../model';

import { RenderableOutputsMergeView } from './output';

import {
  createCheckbox,
  UNCHANGED_MERGE_CLASS,
  ONEWAY_LOCAL_CLASS,
  ONEWAY_REMOTE_CLASS,
  TWOWAY_ADDITION_CLASS,
  TWOWAY_DELETION_CLASS,
  MERGE_CLASSES,
} from './common';

export const CELLMERGE_CLASS = 'jp-Cell-merge';
const CELL_HEADER_CLASS = 'jp-Merge-cellHeader';
const CELL_HEADER_TITLE_CLASS = 'jp-Merge-cellHeader-title';

const MARKED_DELETE = 'jp-mod-todelete';
const MARKED_CLEAR_OUTPUTS = 'jp-mod-clearoutputs';
const CLEAR_OUTPUT_TOGGLE_CLASS = 'jp-Merge-clearOutput-toggle';
const DELETE_CELL_TOGGLE_CLASS = 'jp-Merge-delete-cell-toggle';

const EXECUTIONCOUNT_ROW_CLASS = 'jp-Cellrow-executionCount';
const SOURCE_ROW_CLASS = 'jp-Cellrow-source';
const METADATA_ROW_CLASS = 'jp-Cellrow-metadata';
const OUTPUTS_ROW_CLASS = 'jp-Cellrow-outputs';

const OUTPUTS_CONFLICTED_CLASS = 'jp-conflicted-outputs';
const MARK_OUTPUTS_RESOLVED_CLASS = 'jp-conflicted-outputs-button';
const CELL_ID_CONFLICTED_CLASS = 'jp-conflicted-cellId';

export interface ICellMergeViewOptions {
  local: IStringDiffModel | null;
  remote: IStringDiffModel | null;
  merged: IDiffModel;
  readOnly?: boolean;
  editorClasses: string[];
  editorFactory?: CodeEditor.Factory;
}

/**
 * CellMergeWidget for cell changes
 */
export class CellMergeWidget extends MergePanel<CellMergeModel> {
  static createMergeView({
    merged,
    editorFactory,
    readOnly,
    ...others
  }: ICellMergeViewOptions & IMergeViewOptions): Widget | null {
    let view: Widget | null = null;
    if (merged instanceof StringDiffModel) {
      view = createNbdimeMergeView({
        merged,
        readOnly: readOnly ?? false,
        factory: editorFactory,
        ...others,
      });
    }
    return view;
  }

  protected static getOutputs(
    models: OutputDiffModel[],
    base?: boolean,
  ): nbformat.IOutput[] {
    let raw: nbformat.IOutput[] = [];
    for (let m of models) {
      if (base === true) {
        if (m.base) {
          raw.push(m.base);
        }
      } else {
        if (m.remote) {
          raw.push(m.remote);
        }
      }
    }
    return raw;
  }

  /**
   *
   */
  constructor({
    rendermime,
    mimetype,
    ...options
  }: ICellDiffWidgetOptions<CellMergeModel>) {
    super(options);
    this.addClass(CELLMERGE_CLASS);
    this._rendermime = rendermime;
    this._trans = this._translator.load('nbdime');
    this.mimetype = mimetype;

    this.init();
  }

  validateMerged(candidate: nbformat.ICell): nbformat.ICell {
    if (this.sourceView && this.sourceView instanceof MergeView) {
      let text = this.sourceView.getMergedValue();
      let lines = splitLines(text);
      if (candidate.source !== lines) {
        candidate.source = lines;
      }
    }
    if (this.metadataView && this.metadataView instanceof MergeView) {
      let text = this.metadataView.getMergedValue();
      if (JSON.stringify(candidate.metadata) !== text) {
        // This will need to be validated server side,
        // and should not be touched by client side
        // (structure might differ from assumed form)
        candidate.metadata = JSON.parse(text);
      }
    }
    if (nbformat.isCode(candidate) && this.outputViews) {
      let model = this.outputViews.merged;
      let outputs = model.toJSON();
      candidate.outputs = outputs;
    }
    return candidate;
  }

  protected init() {
    let model = this.model;
    let CURR_CLASSES = MERGE_CLASSES.slice(); // copy

    this.createHeader();

    // Mark cells that have no changes:
    if (
      model.merged.unchanged &&
      model.local &&
      model.local.unchanged &&
      model.remote &&
      model.remote.unchanged
    ) {
      this.addClass(UNCHANGED_MERGE_CLASS);
    }

    /*
     Two different display layouts depending on cell merge type:
     1. Unchanged or one way insert/delete of cell, or identical insert/delete:
        Single r/w editor (merged), with appropriate coloring for insert/delete
     2. Everything else:
        Full 4x merge view
    */
    let ladd = model.local && model.local.added;
    let ldel = model.local && model.local.deleted;
    let radd = model.remote && model.remote.added;
    let rdel = model.remote && model.remote.deleted;
    if ((ladd && !radd) || (ldel && !rdel)) {
      this.headerTitle = ladd
        ? this._trans.__('Cell added locally')
        : this._trans.__('Cell deleted locally');
    } else if ((radd && !ladd) || (rdel && !ldel)) {
      this.headerTitle = radd
        ? this._trans.__('Cell added remotely')
        : this._trans.__('Cell deleted remotely');
    }

    if (
      model.local === null ||
      model.remote === null || // One sided change
      (model.local.unchanged &&
        model.remote.unchanged &&
        model.merged.unchanged) || // Unchanged
      model.local.added !== model.remote.added || // Onesided addition
      (model.local.deleted && model.remote.unchanged) || // Onesided deletion (other side unchanged)
      (model.local.unchanged && model.remote.deleted) || // Onesided deletion (other side unchanged)
      (model.local.added && model.agreedCell) || // Identical additions
      (model.local.deleted && model.remote.deleted) // Deletion on both
    ) {
      CURR_CLASSES = CURR_CLASSES.slice(1, 3);
      // Add single view of source:
      let view = CellDiffWidget.createView({
        model: model.merged.source,
        parent: model.merged,
        editorClasses: CURR_CLASSES,
        rendermime: this._rendermime,
        editorFactory: this._editorFactory,
        translator: this._translator,
      });
      if ((ladd && !radd) || (ldel && !rdel)) {
        this.addClass(ONEWAY_LOCAL_CLASS);
      } else if ((radd && !ladd) || (rdel && !ldel)) {
        this.addClass(ONEWAY_REMOTE_CLASS);
      } else if (ldel && rdel) {
        this.headerTitle = this._trans.__('Deleted on both sides');
        this.addClass(TWOWAY_DELETION_CLASS);
      } else if (ladd && radd) {
        this.headerTitle = this._trans.__('Added on both sides');
        this.addClass(TWOWAY_ADDITION_CLASS);
      }
      view.addClass(SOURCE_ROW_CLASS);
      this.addWidget(view);

      if (hasEntries(model.merged.outputs)) {
        // Add single view of rendered output
        let container = new Panel();
        for (let m of model.merged.outputs) {
          view = CellDiffWidget.createView({
            model: m,
            parent: model.merged,
            editorClasses: CURR_CLASSES,
            rendermime: this._rendermime,
            editorFactory: this._editorFactory,
            translator: this._translator,
          });
          container.addWidget(view);
        }
        container.addClass(OUTPUTS_ROW_CLASS);
        this.addWidget(container);
      }
    } else {
      // Setup full 4-way mergeview of source, metadata and outputs
      // as needed (if changed). Source/metadata/output are each a "row"
      let execDec = model.getExecutionCountDecision();
      if (execDec && execDec.action === 'clear') {
        let row = new FlexPanel({ direction: 'left-to-right' });
        row.addClass(EXECUTIONCOUNT_ROW_CLASS);
        let textWidget = new Widget();
        textWidget.node.textContent = this._trans.__(
          'Execution count will be cleared.',
        );
        row.addWidget(textWidget);
        this.addWidget(row);
      }
      let idDec = model.getCellIdDecision();
      if (idDec && idDec.conflict) {
        this.headerTitle = this._trans.__(
          'Cell has conflicting IDs! Use a text editor to edit the value (base value kept).',
        );
        this.addClass(CELL_ID_CONFLICTED_CLASS);
      }
      let sourceView: Widget | null = null;
      if (
        model.local &&
        model.local.source.unchanged &&
        model.remote &&
        model.remote.source.unchanged &&
        model.merged.source.unchanged
      ) {
        // Use single unchanged view of source
        sourceView = CellDiffWidget.createView({
          model: model.merged.source,
          parent: model.merged,
          editorClasses: CURR_CLASSES,
          rendermime: this._rendermime,
          editorFactory: this._editorFactory,
          translator: this._translator,
        });
      } else {
        sourceView = CellMergeWidget.createMergeView({
          local: model.local ? model.local.source : null,
          remote: model.remote ? model.remote.source : null,
          merged: model.merged.source,
          editorClasses: CURR_CLASSES,
          editorFactory: this._editorFactory,
          translator: this._translator,
          ...this._viewOptions,
        });
      }
      if (sourceView === null) {
        throw new Error('Was not able to create merge view for cell!');
      }
      this.sourceView = sourceView;
      sourceView.addClass(SOURCE_ROW_CLASS);
      this.addWidget(sourceView);

      let metadataChanged = false;
      let outputsChanged = false;
      for (let m of model.subModels) {
        if (!m || m.deleted) {
          // Don't consider deleted cells
          continue;
        }
        metadataChanged =
          metadataChanged || (!!m.metadata && !m.metadata.unchanged);

        if (m.outputs && m.outputs.length > 0) {
          for (let o of m.outputs) {
            outputsChanged = outputsChanged || !o.unchanged;
          }
        }
      }

      if (metadataChanged) {
        let metadataView = CellMergeWidget.createMergeView({
          local: model.local ? model.local.metadata : null,
          remote: model.remote ? model.remote.metadata : null,
          merged: model.merged.metadata,
          editorClasses: CURR_CLASSES,
          editorFactory: this._editorFactory,
          translator: this._translator,
          ...this._viewOptions,
          readOnly: true, // Do not allow manual edit of metadata
        });
        if (metadataView === null) {
          throw new Error(
            'Was not able to create merge view for cell metadata!',
          );
        }
        this.metadataView = metadataView;
        let container = new Panel();
        container.addWidget(metadataView);

        let header = this._trans.__('Metadata changed');
        let collapser = new CollapsiblePanel(container, header, true);
        collapser.addClass(METADATA_ROW_CLASS);
        this.addWidget(collapser);
      }
      if (outputsChanged || hasEntries(model.merged.outputs)) {
        // We know here that we have code cell
        // -> all have outputs !== null
        let baseOut = CellMergeWidget.getOutputs(
          model.local ? model.local.outputs! : [],
          true,
        );
        let localOut = CellMergeWidget.getOutputs(
          model.local ? model.local.outputs! : [],
        );
        let remoteOut = CellMergeWidget.getOutputs(
          model.remote ? model.remote.outputs! : [],
        );
        let mergedOut = CellMergeWidget.getOutputs(model.merged.outputs!);
        let view = new RenderableOutputsMergeView(
          mergedOut,
          MERGE_CLASSES,
          this._rendermime,
          baseOut,
          remoteOut,
          localOut,
          this._viewOptions.showBase,
        );
        this.outputViews = view;

        let header = outputsChanged
          ? model.outputsConflicted
            ? this._trans.__('Outputs conflicted')
            : this._trans.__('Outputs changed')
          : this._trans.__('Outputs unchanged');
        let collapser = new CollapsiblePanel(view, header, !outputsChanged);
        collapser.addClass(OUTPUTS_ROW_CLASS);

        if (model.outputsConflicted) {
          collapser.addClass(OUTPUTS_CONFLICTED_CLASS);
          let conflictClearBtn = new Widget();
          conflictClearBtn.addClass(MARK_OUTPUTS_RESOLVED_CLASS);
          let node = conflictClearBtn.node;
          let btn = document.createElement('button');
          btn.onclick = (ev: MouseEvent) => {
            if (ev.button !== 0) {
              return; // Only main button clicks
            }
            model.clearOutputConflicts();
            collapser.removeClass(OUTPUTS_CONFLICTED_CLASS);
            collapser.headerTitle = this._trans.__('Outputs changed');
            ev.preventDefault();
            ev.stopPropagation();
            conflictClearBtn.parent = null!;
          };
          btn.textContent = this._trans.__('Mark resolved');
          node.appendChild(btn);
          collapser.header.insertWidget(1, conflictClearBtn);
        }

        this.addWidget(collapser);
      }
    }
  }

  protected createHeader(): void {
    let header = new Panel();
    header.addClass(CELL_HEADER_CLASS);

    // Add drag handle
    let w = DragPanel.createDefaultHandle();
    header.addWidget(w);

    // Add title widget
    w = new Widget();
    this.headerTitleWidget = w;
    w.addClass(CELL_HEADER_TITLE_CLASS);
    header.addWidget(w);

    if (hasEntries(this.model.merged.outputs)) {
      // Add "clear outputs" checkbox
      let clearOutputToggle = this._createClearOutputToggle();
      header.addWidget(clearOutputToggle);
    }

    // Add "delete cell" checkbox
    let deleteToggle = this._createDeleteToggle();
    header.addWidget(deleteToggle);

    // Add header to widget
    this.addWidget(header);
    this.header = header;
  }

  private _createClearOutputToggle(): Widget {
    let { checkbox, widget } = createCheckbox(
      this.model.clearOutputs,
      this._trans.__('Clear outputs'),
    );
    if (this.model.clearOutputs) {
      this.addClass(MARKED_CLEAR_OUTPUTS);
    }
    // Map checkbox -> model
    checkbox.onchange = event => {
      this.model.clearOutputs = checkbox.checked;
      this.toggleClass(MARKED_CLEAR_OUTPUTS, checkbox.checked);
    };
    // Map model -> checkbox
    this.model.clearOutputsChanged.connect((_model, value) => {
      checkbox.checked = value;
      this.toggleClass(MARKED_CLEAR_OUTPUTS, value);
    });
    widget.addClass(CLEAR_OUTPUT_TOGGLE_CLASS);
    return widget;
  }

  private _createDeleteToggle(): Widget {
    let { checkbox, widget } = createCheckbox(
      this.model.deleteCell,
      this._trans.__('Delete cell'),
    );
    if (this.model.deleteCell) {
      this.addClass(MARKED_DELETE);
    }
    // Map checkbox -> model
    checkbox.onchange = event => {
      this.model.deleteCell = checkbox.checked;
      this.toggleClass(MARKED_DELETE, checkbox.checked);
    };
    // Map model -> checkbox
    this.model.deleteCellChanged.connect((_model, value) => {
      checkbox.checked = value;
      this.toggleClass(MARKED_DELETE, value);
    });
    widget.addClass(DELETE_CELL_TOGGLE_CLASS);
    return widget;
  }

  mimetype: string;

  header: Panel;
  headerTitleWidget: Widget;

  sourceView: Widget | null = null;
  metadataView: Widget | null = null;
  outputViews: RenderableOutputsMergeView | null = null;

  set headerTitle(value: string) {
    this.headerTitleWidget.node.innerText = value;
  }

  /**
   * Get the model for the widget.
   *
   * #### Notes
   * This is a read-only property.
   */
  get model(): CellMergeModel {
    return this._model;
  }

  private _rendermime: IRenderMimeRegistry;
  protected _trans: TranslationBundle;
}
