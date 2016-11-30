// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
'use strict';

import {
  IRenderMime
} from 'jupyterlab/lib/rendermime';

import {
  nbformat
} from 'jupyterlab/lib/notebook/notebook/nbformat';

import {
  Widget
} from 'phosphor/lib/ui/widget';

import {
  Panel
} from 'phosphor/lib/ui/panel';

import {
  CollapsiblePanel
} from '../../common/collapsiblepanel';

import {
  DragPanel
} from '../../common/dragpanel';

import {
  createNbdimeMergeView
} from '../../common/mergeview';

import {
  IStringDiffModel, StringDiffModel, IDiffModel, OutputDiffModel
} from '../../diff/model';

import {
  CellDiffWidget
} from '../../diff/widget';

import {
  FlexPanel
} from '../../upstreaming/flexpanel';

import {
  CellMergeModel
} from '../model';

import {
  RenderableOutputsMergeView
} from './output';

import {
  ONEWAY_LOCAL_CLASS, ONEWAY_REMOTE_CLASS,
  TWOWAY_ADDITION_CLASS, TWOWAY_DELETION_CLASS,
  MERGE_CLASSES
} from './common';


const CELLMERGE_CLASS = 'jp-Cell-merge';
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



/**
 * CellMergeWidget for cell changes
 */
export
class CellMergeWidget extends Panel {

  static createMergeView(local: IDiffModel, remote: IDiffModel, merged: IDiffModel,
                         editorClasses: string[]): Widget | null {
    let view: Widget | null = null;
    if (merged instanceof StringDiffModel) {
      view = createNbdimeMergeView(remote as IStringDiffModel, editorClasses,
        local as IStringDiffModel, merged);
    }
    return view;
  }

  protected static getOutputs(models: OutputDiffModel[], base?: boolean): nbformat.IOutput[] {
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

  protected static createCheckbox(value: boolean, text: string): {
      checkbox: HTMLInputElement, widget: Widget } {
    let checkbox = document.createElement('input');
    checkbox.setAttribute('type', 'checkbox');
    checkbox.checked = value;
    // Create label for checkbox:
    let widget = new Widget();
    let label = document.createElement('label');
    label.innerText = text;
    // Combine checkbox and label:
    label.insertBefore(checkbox, label.childNodes[0]);
    // Add checkbox to header:
    widget.node.appendChild(label);
    return {checkbox, widget};
  }

  /**
   *
   */
  constructor(model: CellMergeModel, rendermime: IRenderMime,
              mimetype: string) {
    super();
    this.addClass(CELLMERGE_CLASS);
    this._model = model;
    this._rendermime = rendermime;
    this.mimetype = mimetype;

    this.init();
  }

  protected init() {
    let model = this.model;
    let CURR_CLASSES = MERGE_CLASSES.slice();  // copy

    this.createHeader();

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
    if (ladd && !radd || ldel && !rdel) {
      this.headerTitle = ladd ? 'Cell added locally' : 'Cell deleted locally';
    } else if (radd && !ladd || rdel && !ldel) {
      this.headerTitle = radd ? 'Cell added remotely' : 'Cell deleted remotely';
    }

    if (model.local === null || model.remote === null || (  // One sided change
          model.local.unchanged && model.remote.unchanged &&
          model.merged.unchanged) ||  // Unchanged
          model.local.added !== model.remote.added ||  // Onesided addition
          model.local.deleted && model.remote.unchanged ||  // Onesided deletion (other side unchanged)
          model.local.unchanged && model.remote.deleted ||  // Onesided deletion (other side unchanged)
          model.local.added && model.agreedCell || // Identical additions
          model.local.deleted && model.remote.deleted   // Deletion on both
          ) {
      // Add single view of source:
      let view = CellDiffWidget.createView(
        model.merged.source, model.merged, CURR_CLASSES, this._rendermime);
      if (ladd && !radd || ldel && !rdel) {
        this.addClass(ONEWAY_LOCAL_CLASS);
      } else if (radd && !ladd || rdel && !ldel) {
        this.addClass(ONEWAY_REMOTE_CLASS);
      } else if (ldel && rdel) {
        this.headerTitle = 'Deleted on both sides';
        this.addClass(TWOWAY_DELETION_CLASS);
      } else if (ladd && radd) {
        this.headerTitle = 'Added on both sides';
        this.addClass(TWOWAY_ADDITION_CLASS);
      }
      view.addClass(SOURCE_ROW_CLASS);
      this.addWidget(view);
    } else {
      // Setup full 4-way mergeview of source, metadata and outputs
      // as needed (if changed). Source/metadata/output are each a "row"
      let execDec = model.getExecutionCountDecision();
      if (execDec && execDec.action === 'clear') {
        let row = new FlexPanel({direction: 'left-to-right'});
        row.addClass(EXECUTIONCOUNT_ROW_CLASS);
        let textWidget = new Widget();
        textWidget.node.innerText = 'Execution count will be cleared.';
        row.addWidget(textWidget);
        this.addWidget(row);
      }
      let sourceView: Widget | null = null;
      if (model.local.source.unchanged && model.remote.source.unchanged &&
          model.merged.source.unchanged) {
        // Use single unchanged view of source
        sourceView = CellDiffWidget.createView(
          model.merged.source, model.merged, CURR_CLASSES, this._rendermime);
      } else {
        sourceView = CellMergeWidget.createMergeView(
          model.local.source,
          model.remote.source,
          model.merged.source,
          CURR_CLASSES);
      }
      if (sourceView === null) {
        throw new Error('Was not able to create merge view for cell!');
      }
      sourceView.addClass(SOURCE_ROW_CLASS);
      this.addWidget(sourceView);

      let metadataChanged = false;
      let outputsChanged = false;
      for (let m of model.subModels) {
        if (!m || m.deleted) {
          // Don't consider deleted cells
          continue;
        }
        metadataChanged = metadataChanged || (
          !!m.metadata && !m.metadata.unchanged);

        if (m.outputs && m.outputs.length > 0) {
          for (let o of m.outputs) {
            outputsChanged = outputsChanged || !o.unchanged;
          }
        }
      }

      if (metadataChanged) {
        let metadataView = CellMergeWidget.createMergeView(
            model.local.metadata,
            model.remote.metadata,
            model.merged.metadata,
            CURR_CLASSES);
        if (metadataView === null) {
          throw new Error('Was not able to create merge view for cell metadata!');
        }
        let container = new Panel();
        container.addWidget(metadataView);

        let header = 'Metadata changed';
        let collapser = new CollapsiblePanel(container, header, true);
        collapser.addClass(METADATA_ROW_CLASS);
        this.addWidget(collapser);
      }
      if (outputsChanged || model.merged.outputs && model.merged.outputs.length > 0) {
        // We know here that we have code cell
        // -> all have outputs !== null
        let baseOut = CellMergeWidget.getOutputs(model.local.outputs!, true);
        let localOut = CellMergeWidget.getOutputs(model.local.outputs!);
        let remoteOut = CellMergeWidget.getOutputs(model.remote.outputs!);
        let mergedOut = CellMergeWidget.getOutputs(model.merged.outputs!);
        let view = new RenderableOutputsMergeView(
          mergedOut, MERGE_CLASSES, this._rendermime,
          baseOut, remoteOut, localOut);

        let header = outputsChanged ? 'Outputs changed' : 'Outputs unchanged';
        let collapser = new CollapsiblePanel(view, header, !outputsChanged);
        collapser.addClass(OUTPUTS_ROW_CLASS);
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

    // Add "clear outputs" checkbox
    let clearOutputToggle = this._createClearOutputToggle();
    header.addWidget(clearOutputToggle);

    // Add "delete cell" checkbox
    let deleteToggle = this._createDeleteToggle();
    header.addWidget(deleteToggle);

    // Add header to widget
    this.addWidget(header);
    this.header = header;
  }

  private _createClearOutputToggle(): Widget {
    let {checkbox, widget} = CellMergeWidget.createCheckbox(
      this.model.clearOutputs, 'Clear outputs');
    if (this.model.clearOutputs) {
      this.addClass(MARKED_CLEAR_OUTPUTS);
    }
    // Map checkbox -> model
    checkbox.onchange = (event) => {
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
    let {checkbox, widget} = CellMergeWidget.createCheckbox(
      this.model.deleteCell, 'Delete cell');
    if (this.model.deleteCell) {
      this.addClass(MARKED_DELETE);
    }
    // Map checkbox -> model
    checkbox.onchange = (event) => {
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

  private _model: CellMergeModel;
  private _rendermime: IRenderMime;

}
