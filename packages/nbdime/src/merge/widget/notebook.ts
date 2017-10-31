// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
'use strict';

import {
  nbformat
} from '@jupyterlab/coreutils';

import {
  RenderMime
} from '@jupyterlab/rendermime';

import {
  DragDropPanel
} from '../../common/dragpanel';

import {
  hasEntries, deepCopy
} from '../../common/util';

import {
  FlexPanel
} from '../../upstreaming/flexpanel';

import {
  NotebookMergeModel
} from '../model';

import {
  MetadataMergeWidget
} from './metadata';

import {
  CellMergeWidget
} from './cell';

import {
  createCheckbox
} from './common';


const NBMERGE_CLASS = 'jp-Notebook-merge';
const NB_MERGE_CONTROLS_CLASS = 'jp-Merge-notebook-controls';


/**
 * NotebookMergeWidget
 */
export
class NotebookMergeWidget extends DragDropPanel {
  constructor(model: NotebookMergeModel,
              rendermime: RenderMime) {
    super();
    this._model = model;
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
    this.addWidget(new NotebookMergeControls(model));
    work = work.then(() => {
      if (model.metadata) {
        this.metadataWidget = new MetadataMergeWidget(model.metadata);
        this.addWidget(this.metadataWidget);
      }
    });
    this.cellWidgets = [];
    for (let c of model.cells) {
      work = work.then(() => {
        return new Promise<void>((resolve) => {
          let w = new CellMergeWidget(c, rendermime, model.mimetype);
          this.cellWidgets.push(w);
          this.addWidget(w);
          // This limits us to drawing 60 cells per second, which shoudln't
          // be a problem...
          requestAnimationFrame(() => {
            resolve();
          });
        });
      });
    }
    return work;
  }

  validateMerged(candidate: nbformat.INotebookContent): nbformat.INotebookContent {
    let validated = deepCopy(candidate);
    // Validate metadata
    if (this.metadataWidget) {
      validated.metadata = this.metadataWidget.validateMerged(candidate.metadata);
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

  protected move(from: number, to: number): void {
    // Move cell in model list
    this._model.cells.splice(to, 0, this._model.cells.splice(from, 1)[0]);
    super.move(from, to);
  }

  protected metadataWidget: MetadataMergeWidget | null = null;
  protected cellWidgets: CellMergeWidget[];

  private _model: NotebookMergeModel;
  private _rendermime: RenderMime;
}


/**
 * Collection of notebook-wide controls
 */
class NotebookMergeControls extends FlexPanel {
  constructor(model: NotebookMergeModel) {
    super({
      direction: 'left-to-right'
    });
    this.model = model;
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
    let chk = createCheckbox(false, 'Clear <i>all</i> cell outputs');
    this.clearOutputsToggle = chk.checkbox;
    this.addWidget(chk.widget);

    // Add "Clear all conflicted outputs" checkbox
    chk = createCheckbox(false, 'Clear <i>conflicted</i> cell outputs');
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
          if (conflicted === null ) {
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
      this.clearConflictedOutputsToggle.parentElement!.setAttribute('disabled', '');
    } else {
      this.clearConflictedOutputsToggle.parentElement!.removeAttribute('disabled');
    }
  }

  clearOutputsToggle: HTMLInputElement;

  clearConflictedOutputsToggle: HTMLInputElement;

  model: NotebookMergeModel;
}
