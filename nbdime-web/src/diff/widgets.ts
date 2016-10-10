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
  Panel, PanelLayout
} from 'phosphor/lib/ui/panel';

import {
  createNbdimeMergeView
} from '../common/mergeview';

import {
  CollapsiblePanel
} from '../common/collapsiblepanel';

import {
  valueIn
} from '../common/util';

import {
  CellDiffModel, NotebookDiffModel, IDiffModel,
  IStringDiffModel, StringDiffModel, OutputDiffModel
} from './model';


const NBDIFF_CLASS = 'jp-Notebook-diff';

const ROOT_METADATA_CLASS = 'jp-Metadata-diff';
const CELLDIFF_CLASS = 'jp-Cell-diff';

const SOURCE_ROW_CLASS = 'jp-Cellrow-source';
const METADATA_ROW_CLASS = 'jp-Cellrow-metadata';
const OUTPUTS_ROW_CLASS = 'jp-Cellrow-outputs';

const TWOWAY_DIFF_CLASS = 'jp-Diff-twoway';
const ADDED_DIFF_CLASS = 'jp-Diff-added';
const DELETED_DIFF_CLASS = 'jp-Diff-deleted';
const UNCHANGED_DIFF_CLASS = 'jp-Diff-unchanged';

const DIFF_CLASSES = ['jp-Diff-base', 'jp-Diff-remote'];


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
 * A list of MIME types that can be shown as string diff.
 */
const stringDiffMimeTypes = ['text/html', 'text/plain'];



/**
 * Widget for outputs with renderable MIME data.
 */
class RenderableOutputView extends Widget {
  constructor(model: OutputDiffModel, editorClass: string[],
              rendermime: IRenderMime) {
    super();
    this._rendermime = rendermime;
    let bdata = model.base as nbformat.IOutput;
    let rdata = model.remote as nbformat.IOutput;
    this.layout = new PanelLayout();

    let ci = 0;
    if (bdata) {
      let widget = this.createOutput(bdata, false);
      (this.layout as PanelLayout).addWidget(widget);
      widget.addClass(editorClass[ci++]);
    }
    if (rdata && rdata !== bdata) {
      let widget = this.createOutput(rdata, false);
      (this.layout as PanelLayout).addWidget(widget);
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
      if (valueIn(o.output_type, ['execute_result', 'display_data'])) {
        let bundle = (o as any).data as nbformat.MimeBundle;
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

/**
 * CellDiffWidget for cell changes
 */
export
class CellDiffWidget extends Panel {
  /**
   *
   */
  constructor(model: CellDiffModel, rendermime: IRenderMime,
              mimetype: string) {
    super();
    this.addClass(CELLDIFF_CLASS);
    this._model = model;
    this._rendermime = rendermime;
    this.mimetype = mimetype;

    this.init();
  }

  protected init() {
    let model = this.model;

    // Add 'cell added/deleted' notifiers, as appropriate
    let CURR_DIFF_CLASSES = DIFF_CLASSES.slice();  // copy
    if (model.added) {
      let widget = new Widget();
      widget.node.textContent = 'Cell added';
      this.addWidget(widget);
      this.addClass(ADDED_DIFF_CLASS);
      CURR_DIFF_CLASSES = DIFF_CLASSES.slice(0, 1);
    } else if (model.deleted) {
      let widget = new Widget();
      widget.node.textContent = 'Cell deleted';
      this.addWidget(widget);
      this.addClass(DELETED_DIFF_CLASS);
      CURR_DIFF_CLASSES = DIFF_CLASSES.slice(1, 2);
    } else if (model.unchanged) {
      this.addClass(UNCHANGED_DIFF_CLASS);
    } else {
      this.addClass(TWOWAY_DIFF_CLASS);
    }

    // Add inputs and outputs, on a row-by-row basis
    let ctor = this.constructor as typeof CellDiffWidget;
    let sourceView = ctor.createView(
      model.source, model, CURR_DIFF_CLASSES, this._rendermime);
    sourceView.addClass(SOURCE_ROW_CLASS);
    this.addWidget(sourceView);

    if (model.metadata && !model.metadata.unchanged) {
      let metadataView = ctor.createView(
        model.metadata, model, CURR_DIFF_CLASSES, this._rendermime);
      metadataView.addClass(METADATA_ROW_CLASS);
      this.addWidget(metadataView);
    }
    if (model.outputs && model.outputs.length > 0) {
      let container = new Panel();
      let changed = false;
      for (let o of model.outputs) {
        let outputsWidget = ctor.createView(
          o, model, CURR_DIFF_CLASSES, this._rendermime);
        container.addWidget(outputsWidget);
        changed = changed || !o.unchanged || o.added || o.deleted;
      }
      let collapsed = !changed || model.added || model.deleted;
      let header = changed ? 'Outputs changed' : 'Outputs unchanged';
      let collapser = new CollapsiblePanel(container, header, collapsed);
      collapser.addClass(OUTPUTS_ROW_CLASS);
      this.addWidget(collapser);
    }
  }

  /**
   * Create a new sub-view.
   */
  static
  createView(model: IDiffModel, parent: CellDiffModel,
             editorClasses: string[], rendermime: IRenderMime): Widget {
    let view: Widget = null;
    if (model instanceof StringDiffModel) {
      if (model.unchanged && parent.cellType === 'markdown') {
        view = rendermime.render({bundle: {'text/markdown': model.base}});
      } else {
        view = createNbdimeMergeView(model as IStringDiffModel, editorClasses);
      }
    } else if (model instanceof OutputDiffModel) {
      // Take one of three actions, depending on output types
      // 1) Text-type output: Show a MergeView with text diff.
      // 2) Renderable types: Side-by-side comparison.
      // 3) Unknown types: Stringified JSON diff.
      let tmodel = model as OutputDiffModel;
      let renderable = RenderableOutputView.canRenderUntrusted(tmodel);
      for (let mt of rendermime.order) {
        let key = tmodel.hasMimeType(mt);
        if (key) {
          if (!renderable || valueIn(mt, stringDiffMimeTypes)) {
            view = createNbdimeMergeView(tmodel.stringify(key), editorClasses);
          } else if (renderable) {
            view = new RenderableOutputView(tmodel, editorClasses, rendermime);
          }
          break;
        }
      }
      if (!view) {
        view = createNbdimeMergeView(tmodel.stringify(), editorClasses);
      }
    } else {
      throw 'Unrecognized model type.';
    }
    if (model.collapsible) {
      view = new CollapsiblePanel(
          view, model.collapsibleHeader, model.startCollapsed);
    }
    let container = new Panel();
    if (model.added && !parent.added) {
      // Implies this is added output
      let addSpacer = new Widget();
      addSpacer.node.textContent = 'Output added';
      container.addWidget(addSpacer);
      container.addClass(ADDED_DIFF_CLASS);
    } else if (model.deleted && !parent.deleted) {
      // Implies this is deleted output
      let delSpacer = new Widget();
      delSpacer.node.textContent = 'Output deleted';
      container.addWidget(delSpacer);
      container.addClass(DELETED_DIFF_CLASS);
    } else if (model.unchanged) {
      container.addClass(UNCHANGED_DIFF_CLASS);
    } else {
      container.addClass(TWOWAY_DIFF_CLASS);
    }
    container.addWidget(view);
    return container;
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

  protected _model: CellDiffModel = null;
  protected _rendermime: IRenderMime = null;
}


/**
 * MetadataWidget for changes to Notebook-level metadata
 */
export
class MetadataDiffWidget extends Panel {
  constructor(model: IStringDiffModel) {
    super();
    this._model = model;
    console.assert(!model.added && !model.deleted);
    this.addClass(ROOT_METADATA_CLASS);
    this.init();
  }

  init() {
    let model = this._model;
    if (!model.unchanged) {
      this.addClass(TWOWAY_DIFF_CLASS);
      let view: Widget = createNbdimeMergeView(
        model, DIFF_CLASSES);
      if (model.collapsible) {
        view = new CollapsiblePanel(
          view, model.collapsibleHeader, model.startCollapsed);
      }
      this.addWidget(view);
    }
  }

  private _model: IStringDiffModel;
}


/**
 * NotebookDiffWidget
 */
export
class NotebookDiffWidget extends Widget {
  constructor(model: NotebookDiffModel, rendermime: IRenderMime) {
    super();
    this._model = model;
    this._rendermime = rendermime;
    let layout = this.layout = new PanelLayout();

    this.addClass(NBDIFF_CLASS);

    if (model.metadata) {
      layout.addWidget(new MetadataDiffWidget(model.metadata));
    }
    for (let c of model.cells) {
      layout.addWidget(new CellDiffWidget(c, rendermime, model.mimetype));
    }
  }

  /**
   * Get the model for the widget.
   *
   * #### Notes
   * This is a read-only property.
   */
  get model(): NotebookDiffModel {
    return this._model;
  }

  private _model: NotebookDiffModel;
  private _rendermime: IRenderMime = null;
}
