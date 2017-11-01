// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.

import expect = require('expect.js');

import {
  nbformat
} from '@jupyterlab/coreutils';

import {
  Widget
} from '@phosphor/widgets';

import {
  RenderMime, defaultRendererFactories
} from '@jupyterlab/rendermime';

import {
  defaultSanitizer
} from '@jupyterlab/apputils';

import {
    IMergeDecision
} from '../../../src/merge/decisions';

import {
    MetadataMergeModel, NotebookMergeModel
} from '../../../src/merge/model';

import {
    CellMergeWidget, NotebookMergeWidget, MetadataMergeWidget
} from '../../../src/merge/widget';


const notebook = require('../../files/base.ipynb.json') as nbformat.INotebookContent;
const NBdecisions = require('../../files/decisionsA.json') as IMergeDecision[];

describe('merge', () => {

  describe('widget', () => {

    let rendermime = new RenderMime({
      initialFactories: defaultRendererFactories, sanitizer: defaultSanitizer});

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
          expect(widget).to.not.be(null);
      });

    });

    describe('NotebookMergeWidget', () => {

      it('should create a widget for a simple realistic model', () => {
          let model = new NotebookMergeModel(notebook, NBdecisions);
          let widget = new NotebookMergeWidget(model, rendermime);
          expect(widget).to.not.be(null);
          Widget.attach(widget, document.body);
      });

    });

  });

});
