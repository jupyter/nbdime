// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
'use strict';

import type { Widget } from '@lumino/widgets';

import { DiffPanel } from '../../common/basepanel';

import { createNbdimeMergeView } from '../../common/mergeview';

import { CollapsiblePanel } from '../../common/collapsiblepanel';

import type { IDiffWidgetOptions } from '../../common/interfaces';

import type { IStringDiffModel } from '../model';

import { TWOWAY_DIFF_CLASS } from './common';

const ROOT_METADATA_CLASS = 'jp-Metadata-diff';

/**
 * MetadataWidget for changes to Notebook-level metadata
 */
export class MetadataDiffWidget extends DiffPanel<IStringDiffModel> {
  constructor(options: IDiffWidgetOptions<IStringDiffModel>) {
    super(options);
    console.assert(!this._model.added && !this._model.deleted);
    this.addClass(ROOT_METADATA_CLASS);
    this.init();
  }

  init() {
    let model = this._model;
    if (!model.unchanged) {
      this.addClass(TWOWAY_DIFF_CLASS);
      let view: Widget = createNbdimeMergeView({
        remote: model,
        factory: this._editorFactory,
        translator: this._translator,
        ...this._viewOptions,
      });
      if (model.collapsible) {
        view = new CollapsiblePanel(
          view,
          model.collapsibleHeader,
          model.startCollapsed,
        );
      }
      this.addWidget(view);
    }
  }
}
