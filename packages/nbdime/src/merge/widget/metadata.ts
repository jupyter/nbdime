// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
'use strict';

import type * as nbformat from '@jupyterlab/nbformat';

import type {
  IDiffWidgetOptions,
  IMergeViewOptions,
} from '../../common/interfaces';

import { createNbdimeMergeView, MergeView } from '../../common/mergeview';

import { CollapsiblePanel } from '../../common/collapsiblepanel';

import { MergePanel } from '../../common/basepanel';

import type { MetadataMergeModel } from '../model';

const ROOT_METADATA_CLASS = 'jp-Metadata-diff';

/**
 * MetadataWidget for changes to Notebook-level metadata
 */
export class MetadataMergeWidget extends MergePanel<MetadataMergeModel> {
  constructor(
    options: IDiffWidgetOptions<MetadataMergeModel> & IMergeViewOptions,
  ) {
    super(options);
    this.addClass(ROOT_METADATA_CLASS);
    this.init();
  }

  init() {
    const model = this._model;

    // We know/assume that MetadataMergeModel never has
    // null values for local/remote:
    this.view = createNbdimeMergeView({
      remote: model.remote,
      local: model.local,
      merged: model.merged,
      factory: this._editorFactory,
      ...this._viewOptions,
    });
    const wrapper = new CollapsiblePanel(
      this.view,
      'Notebook metadata changed',
      true,
    );
    this.addWidget(wrapper);
  }

  validateMerged(
    candidate: nbformat.INotebookMetadata,
  ): nbformat.INotebookMetadata {
    const text = this.view.getMergedValue();
    if (JSON.stringify(candidate) !== text) {
      // This will need to be validated server side,
      // and should not be touched by client side
      // (structure might differ from assumed form)
      candidate = JSON.parse(text);
    }
    return candidate;
  }

  protected view: MergeView;
}
