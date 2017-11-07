// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
'use strict';

import {
  every
} from '@phosphor/algorithm';

import {
  Panel, Widget
} from '@phosphor/widgets';

import {
  RenderMime, MimeModel
} from '@jupyterlab/rendermime';

import {
  createNbdimeMergeView
} from '../../common/mergeview';

import {
  FlexPanel
} from '../../upstreaming/flexpanel';

import {
  CollapsiblePanel
} from '../../common/collapsiblepanel';

import {
  valueIn, hasEntries
} from '../../common/util';

import {
  DIFF_CLASSES, ADDED_DIFF_CLASS, DELETED_DIFF_CLASS,
  TWOWAY_DIFF_CLASS, UNCHANGED_DIFF_CLASS, CHUNK_PANEL_CLASS,
  ADDED_CHUNK_PANEL_CLASS, REMOVED_CHUNK_PANEL_CLASS
} from './common';

import {
  RenderableOutputView
} from './output';

import {
  CellDiffModel, IDiffModel, StringDiffModel, OutputDiffModel,
  ImmutableDiffModel
} from '../model';


/**
 * The class name added to the prompt area of cell.
 */
const PROMPT_CLASS = 'jp-InputPrompt';


export
const CELLDIFF_CLASS = 'jp-Cell-diff';

const EXECUTIONCOUNT_ROW_CLASS = 'jp-Cellrow-executionCount';
const SOURCE_ROW_CLASS = 'jp-Cellrow-source';
const METADATA_ROW_CLASS = 'jp-Cellrow-metadata';
const OUTPUTS_ROW_CLASS = 'jp-Cellrow-outputs';

/**
 * A list of MIME types that can be shown as string diff.
 */
const stringDiffMimeTypes = ['text/html', 'text/plain', 'application/json'];



/**
 * CellDiffWidget for cell changes
 */
export
class CellDiffWidget extends Panel {
  /**
   *
   */
  constructor(model: CellDiffModel, rendermime: RenderMime,
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
    let sourceView = CellDiffWidget.createView(
      model.source, model, CURR_DIFF_CLASSES, this._rendermime);
    sourceView.addClass(SOURCE_ROW_CLASS);
    if (model.executionCount) {
      sourceView.insertWidget(0, CellDiffWidget.createPrompts(
        model.executionCount, model));
    }
    this.addWidget(sourceView);

    if (!model.metadata.unchanged) {
      let metadataView = CellDiffWidget.createView(
        model.metadata, model, CURR_DIFF_CLASSES, this._rendermime);
      metadataView.addClass(METADATA_ROW_CLASS);
      this.addWidget(metadataView);
    }
    const chunks = model.getChunkedOutputs();
    if (hasEntries(chunks)) {
      let container = new Panel();
      let changed = false;
      for (let chunk of chunks) {
        if (chunk.length === 1) {
          let o = chunk[0];
          let outputsWidget = CellDiffWidget.createView(
            o, model, CURR_DIFF_CLASSES, this._rendermime);
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
            let outputsWidget = CellDiffWidget.createView(
              o, model, CURR_DIFF_CLASSES, this._rendermime);
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

  static createPrompts(model: ImmutableDiffModel, parent: CellDiffModel): Panel {
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
    let container = new FlexPanel({direction: 'left-to-right'});
    for (let text of prompts) {
      let w = new Widget();
      w.node.innerText = text;
      w.addClass(PROMPT_CLASS);
      container.addWidget(w);
      FlexPanel.setGrow(w, 1);
    }
    container.addClass(EXECUTIONCOUNT_ROW_CLASS);
    return container;
  }

  /**
   * Create a new sub-view.
   */
  static
  createView(model: IDiffModel, parent: CellDiffModel,
             editorClasses: string[], rendermime: RenderMime): Panel {
    let view: Widget | null = null;
    if (model instanceof StringDiffModel) {
      if (model.unchanged && parent.cellType === 'markdown') {
        let mimeModel = new MimeModel({ data: {'text/markdown': model.base!} });
        let mimeType = rendermime.preferredMimeType(mimeModel.data, true);
        if (!mimeType) {
          throw new Error('No renderer for output');
        }
        let renderer = rendermime.createRenderer(mimeType);
        renderer.renderModel(mimeModel);
        view = renderer;
      } else {
        view = createNbdimeMergeView(model);
      }
    } else if (model instanceof OutputDiffModel) {
      // Take one of three actions, depending on output types
      // 1) Text-type output: Show a MergeView with text diff.
      // 2) Renderable types: Side-by-side comparison.
      // 3) Unknown types: Stringified JSON diff.
      // If the model is one-sided or unchanged, option 2) is preferred to 1)
      let renderable = RenderableOutputView.canRenderUntrusted(model);
      every(rendermime.mimeTypes, (mt) => {
        let key = model.hasMimeType(mt);
        if (key) {
          if (!renderable ||
              !(model.added || model.deleted || model.unchanged) &&
              valueIn(mt, stringDiffMimeTypes)) {
            // 1.
            view = createNbdimeMergeView(model.stringify(key));
          } else if (renderable) {
            // 2.
            view = new RenderableOutputView(model, editorClasses, rendermime);
          }
          return false;
        }
        return true;
      });
      if (!view) {
        // 3.
        view = createNbdimeMergeView(model.stringify());
      }
    } else {
      throw new Error('Unrecognized model type.');
    }
    if (model.collapsible) {
      view = new CollapsiblePanel(
          view, model.collapsibleHeader, model.startCollapsed);
    }
    let container = new Panel();
    if (model instanceof OutputDiffModel) {
      if (model.added) {
        container.addClass(ADDED_DIFF_CLASS);
      } else if (model.deleted) {
        container.addClass(DELETED_DIFF_CLASS);
      } else if (model.unchanged) {
        container.addClass(UNCHANGED_DIFF_CLASS);
      } else {
        container.addClass(TWOWAY_DIFF_CLASS);
      }
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

  protected _model: CellDiffModel;
  protected _rendermime: RenderMime;
}
