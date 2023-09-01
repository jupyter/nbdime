// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.

import type * as nbformat from '@jupyterlab/nbformat';

import {
  Widget
} from '@lumino/widgets';

import {
  RenderMimeRegistry, standardRendererFactories
} from '@jupyterlab/rendermime';

import {
  Sanitizer,
} from '@jupyterlab/apputils';

import type {
    IMergeDecision
} from '../../../src/merge/decisions';

import {
    MetadataMergeModel, NotebookMergeModel
} from '../../../src/merge/model';

import {
    NotebookMergeWidget, MetadataMergeWidget
} from '../../../src/merge/widget';

import notebook from '../../files/base.ipynb.json';
import NBdecisions from '../../files/decisionsA.json';

describe('merge', () => {

  describe('widget', () => {

    let rendermime = new RenderMimeRegistry({
      initialFactories: standardRendererFactories, sanitizer: new Sanitizer()});

    // End rendermime setup

    describe('MetadataDiffWidget', () => {

      it('should create a widget for an unchanged model', () => {
          let base = {
              kernelspec: {
                  name: '',
                  display_name: ''
              },
              language_info: {
                  name: ''
              },
              orig_nbformat: 4
          } as nbformat.INotebookMetadata;
          let model = new MetadataMergeModel(
              base, []);
          let widget = new MetadataMergeWidget(model);
          expect(widget).not.toBe(null);
      });

    });

    describe('NotebookMergeWidget', () => {

      it('should create a widget for a simple realistic model', () => {
          let model = new NotebookMergeModel(notebook as nbformat.INotebookContent, NBdecisions as IMergeDecision[]);
          let widget = new NotebookMergeWidget(model, rendermime);
          expect(widget).not.toBe(null);
          Widget.attach(widget, document.body);
      });

    });

  });

});
