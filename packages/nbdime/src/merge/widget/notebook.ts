// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
'use strict';

import type * as nbformat from '@jupyterlab/nbformat';

import type { IRenderMimeRegistry } from '@jupyterlab/rendermime';

import type { ITranslator, TranslationBundle } from '@jupyterlab/translation';

import { MergePanel } from '../../common/basepanel';

import type {
  IMergeViewOptions,
  IMimeDiffWidgetOptions,
} from '../../common/interfaces';

import { hasEntries, deepCopy } from '../../common/util';

import { FlexPanel } from '../../upstreaming/flexpanel';

import type { NotebookMergeModel } from '../model';

import { MetadataMergeWidget } from './metadata';

import { CellMergeWidget } from './cell';

import { createCheckbox } from './common';

import { CellsDragDrop, ChunkedCellsWidget } from './dragdrop';

const NBMERGE_CLASS = 'jp-Notebook-merge';
const NB_MERGE_CONTROLS_CLASS = 'jp-Merge-notebook-controls';

/**
 * NotebookMergeWidget
 */
export class NotebookMergeWidget extends MergePanel<NotebookMergeModel> {
  constructor({
    rendermime,
    ...options
  }: IMimeDiffWidgetOptions<NotebookMergeModel> & IMergeViewOptions) {
    super(options);
    this._rendermime = rendermime;

    this.addClass(NBMERGE_CLASS);
  }

  /**
   * Start adding sub-widgets.
   *
   * Separated from constructor to allow 'live' adding of widgets
   */
  init(): Promise<void> {
    let model = this._model;
    let rendermime = this._rendermime;

    let work = Promise.resolve();
    this.addWidget(
      new NotebookMergeControls({ model, translator: this._translator }),
    );
    work = work.then(() => {
      if (model.metadata) {
        this.metadataWidget = new MetadataMergeWidget({
          model: model.metadata,
          editorFactory: this._editorFactory,
          translator: this._translator,
          ...this._viewOptions,
        });
        this.addWidget(this.metadataWidget);
      }
    });
    work = work.then(() => {
      this.cellContainer = new CellsDragDrop({
        acceptDropsFromExternalSource: true,
      });
      this.cellContainer.setFriendlyGroup(CellsDragDrop.makeGroup());
      this.cellContainer.moved.connect(this.onDragDropMove, this);
      this.addWidget(this.cellContainer);
    });
    this.cellWidgets = [];
    let chunk: ChunkedCellsWidget | null = null;
    for (let c of model.cells) {
      work = work.then(() => {
        return new Promise<void>(resolve => {
          let w = new CellMergeWidget({
            model: c,
            rendermime,
            mimetype: model.mimetype,
            editorFactory: this._editorFactory,
            translator: this._translator,
            ...this._viewOptions,
          });
          this.cellWidgets.push(w);
          if (c.onesided && c.conflicted) {
            if (chunk === null) {
              chunk = new ChunkedCellsWidget({ translator: this._translator });
              chunk.cells.moved.connect(this.onDragDropMove, this);
              chunk.resolved.connect(this.onChunkResolved, this);
              this.cellContainer.addToFriendlyGroup(chunk.cells);
            }
            chunk.cells.addWidget(w);
          } else {
            if (chunk !== null) {
              this.cellContainer.addWidget(chunk);
              chunk = null;
            }
            this.cellContainer.addWidget(w);
          }
          // This limits us to drawing 60 cells per second, which shouldn't
          // be a problem...
          requestAnimationFrame(() => {
            resolve();
          });
        });
      });
    }
    work = work.then(() => {
      if (chunk !== null) {
        this.cellContainer.addWidget(chunk);
      }
    });
    return work;
  }

  validateMerged(
    candidate: nbformat.INotebookContent,
  ): nbformat.INotebookContent {
    let validated = deepCopy(candidate);
    // Validate metadata
    if (this.metadataWidget) {
      validated.metadata = this.metadataWidget.validateMerged(
        candidate.metadata,
      );
    }

    // Validate cells
    let i = 0;
    for (let c of this.cellWidgets) {
      if (!c.model.deleteCell) {
        validated.cells[i] = c.validateMerged(candidate.cells[i]);
        ++i;
      }
    }
    return validated;
  }

  /**
   * Get the model for the widget.
   *
   * #### Notes
   * This is a read-only property.
   */
  get model(): NotebookMergeModel {
    return this._model;
  }

  protected onDragDropMove(
    sender: CellsDragDrop,
    args: CellsDragDrop.IMovedArgs,
  ): void {
    // Move cell in model list
    let { widget, oldParent, before, after } = args;
    let from = this._model.cells.indexOf(widget.model);
    let to: number;
    if (after) {
      to = this._model.cells.indexOf(after.model);
    } else if (before) {
      to = this._model.cells.indexOf(before.model) + 1;
    } else {
      throw new Error('Need either before or after');
    }
    if (to > from) {
      to -= 1;
    }
    this._model.cells.splice(to, 0, this._model.cells.splice(from, 1)[0]);
    if (oldParent.widgets.length === 0) {
      let chunk = oldParent.parent! as ChunkedCellsWidget;
      chunk.onResolve();
    }
    // Mark any conflict on a cell moved from chunk as resolved
    if (
      oldParent !== this.cellContainer &&
      widget.parent === this.cellContainer
    ) {
      for (let d of widget.model.decisions) {
        d.conflict = false;
      }
    }
  }

  protected onChunkResolved(sender: ChunkedCellsWidget, args: void): void {
    let index = this.cellContainer.widgets.indexOf(sender);
    while (sender.cells.widgets.length > 0) {
      this.cellContainer.insertWidget(index++, sender.cells.widgets[0]);
    }
    sender.parent = null;
    sender.dispose();
  }

  protected metadataWidget: MetadataMergeWidget | null = null;
  protected cellWidgets: CellMergeWidget[];
  protected cellContainer: CellsDragDrop;

  private _rendermime: IRenderMimeRegistry;
}

/**
 * Collection of notebook-wide controls
 */
class NotebookMergeControls extends FlexPanel {
  constructor({
    model,
    translator,
  }: {
    model: NotebookMergeModel;
    translator: ITranslator;
  }) {
    super({
      direction: 'left-to-right',
    });
    this.model = model;
    this.trans = translator.load('nbdime');
    this.addClass(NB_MERGE_CONTROLS_CLASS);
    let anyOutputs = false;
    for (let cell of model.cells) {
      if (hasEntries(cell.merged.outputs)) {
        anyOutputs = true;
        break;
      }
    }
    if (anyOutputs) {
      this.init_controls();
    }
  }

  init_controls(): void {
    // Add "Clear all outputs" checkbox
    let chk = createCheckbox(false, this.trans.__('Clear all cell outputs'));
    this.clearOutputsToggle = chk.checkbox;
    this.addWidget(chk.widget);

    // Add "Clear all conflicted outputs" checkbox
    chk = createCheckbox(false, this.trans.__('Clear conflicted cell outputs'));
    this.clearConflictedOutputsToggle = chk.checkbox;
    this.addWidget(chk.widget);

    this.updateOutputsToggles();
    this.connectOutputsToggles();
  }

  connectOutputsToggles(): void {
    for (let cell of this.model.cells) {
      if (hasEntries(cell.merged.outputs)) {
        cell.clearOutputsChanged.connect(this.updateOutputsToggles, this);
      }
    }
    this.clearOutputsToggle.addEventListener('change', this);
    this.clearConflictedOutputsToggle.addEventListener('change', this);
  }

  disconnectOutputsToggles(): void {
    for (let cell of this.model.cells) {
      if (hasEntries(cell.merged.outputs)) {
        cell.clearOutputsChanged.disconnect(this.updateOutputsToggles, this);
      }
    }
    this.clearOutputsToggle.removeEventListener('change', this);
    this.clearConflictedOutputsToggle.removeEventListener('change', this);
  }

  handleEvent(event: Event): void {
    switch (event.type) {
      case 'change':
        if (event.currentTarget === this.clearOutputsToggle) {
          this.onClearAllOutputsChanged();
        } else if (event.currentTarget === this.clearConflictedOutputsToggle) {
          this.onClearConflictedOutputsChanged();
        }
        break;
      default:
        break;
    }
  }

  onClearAllOutputsChanged(): void {
    this.disconnectOutputsToggles();
    try {
      let value = this.clearOutputsToggle.checked;
      for (let cell of this.model.cells) {
        if (hasEntries(cell.merged.outputs)) {
          cell.clearOutputs = value;
        }
      }
    } finally {
      this.updateOutputsToggles();
      this.connectOutputsToggles();
    }
  }

  onClearConflictedOutputsChanged(): void {
    this.disconnectOutputsToggles();
    try {
      let value = this.clearConflictedOutputsToggle.checked;
      for (let cell of this.model.cells) {
        if (hasEntries(cell.merged.outputs) && cell.outputsConflicted) {
          cell.clearOutputs = value;
        }
      }
    } finally {
      this.updateOutputsToggles();
      this.connectOutputsToggles();
    }
  }

  updateOutputsToggles(): void {
    // null = indeterminate
    let all: boolean | null | undefined = undefined;
    let conflicted: boolean | null | undefined = undefined;
    for (let cell of this.model.cells) {
      if (hasEntries(cell.merged.outputs)) {
        let current = cell.clearOutputs;
        if (all === null) {
          // Indeterminate, current value won't change it
        } else if (all === undefined) {
          all = current;
        } else if (all !== current) {
          all = null;
        }
        if (cell.outputsConflicted) {
          if (conflicted === null) {
            // Indeterminate, current value won't change it
          } else if (conflicted === undefined) {
            conflicted = current;
          } else if (conflicted !== current) {
            conflicted = null;
          }
        }
      }
      if (conflicted === null && all === null) {
        // Both indeterminate, short circuit
        break;
      }
    }

    this.clearOutputsToggle.checked = all === true;
    this.clearOutputsToggle.indeterminate = all === null;

    this.clearConflictedOutputsToggle.checked = conflicted === true;
    this.clearConflictedOutputsToggle.indeterminate = conflicted === null;
    this.clearConflictedOutputsToggle.disabled = conflicted === undefined;
    if (conflicted === undefined) {
      this.clearConflictedOutputsToggle.parentElement!.setAttribute(
        'disabled',
        '',
      );
    } else {
      this.clearConflictedOutputsToggle.parentElement!.removeAttribute(
        'disabled',
      );
    }
  }

  clearOutputsToggle: HTMLInputElement;

  clearConflictedOutputsToggle: HTMLInputElement;

  model: NotebookMergeModel;

  protected trans: TranslationBundle;
}
