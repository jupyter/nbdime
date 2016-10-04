// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.

import expect = require('expect.js');

import {
  nbformat
} from 'jupyterlab/lib/notebook/notebook/nbformat';

import {
    MetadataMergeModel
} from '../../../src/merge/model';

import {
    CellMergeWidget, NotebookMergeWidget, MetadataMergeWidget
} from '../../../src/merge/widget';


describe('merge', () => {

  describe('widget', () => {

    describe('MetadataDiffWidget', () => {

      it('should create a widget for an unchanged model', () => {
          let base: nbformat.INotebookMetadata = {
              kernelspec: {
                  name: '',
                  display_name: ''
              },
              language_info: {
                  name: ''
              },
              orig_nbformat: 4
          };
          let model = new MetadataMergeModel(
              base, [], 'application/json');
          let widget = new MetadataMergeWidget(model);
          expect(widget).to.not.be(null);
      });

    });

  });

});
