// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.

import expect = require('expect.js');

import {
  nbformat
} from '@jupyterlab/services';

import {
  RenderMime
} from 'jupyterlab/lib/rendermime';

import {
  HTMLRenderer, LatexRenderer, ImageRenderer, TextRenderer,
  JavascriptRenderer, SVGRenderer, MarkdownRenderer
} from 'jupyterlab/lib/renderers';

import {
  defaultSanitizer
} from 'jupyterlab/lib/sanitizer';

import {
  Widget
} from 'phosphor/lib/ui/widget';

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

    // Setup rendermime:
    const transformers = [
      new JavascriptRenderer(),
      new MarkdownRenderer(),
      new HTMLRenderer(),
      new ImageRenderer(),
      new SVGRenderer(),
      new LatexRenderer(),
      new TextRenderer()
    ];

    let renderers: RenderMime.MimeMap<RenderMime.IRenderer> = {};
    let order: string[] = [];
    for (let t of transformers) {
      for (let m of t.mimetypes) {
        renderers[m] = t;
        order.push(m);
      }
    }
    let rendermime = new RenderMime({
      renderers: renderers, order: order, sanitizer: defaultSanitizer});

    // End rendermime setup

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
