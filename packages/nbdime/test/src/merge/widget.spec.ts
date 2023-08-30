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
  defaultSanitizer
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
import type { CodeEditor } from '@jupyterlab/codeeditor';


const notebook = require('../../files/base.ipynb.json') as nbformat.INotebookContent;
const NBdecisions = require('../../files/decisionsA.json') as IMergeDecision[];

// Mock codemirror editor as it is provided by JupyterLab
//  Notes:
//    The signal `selections.changed` must be mocked as it is connected
//    to a slot in CodeEditorWrapper in @jupyterlab/codeeditor
//    See https://github.com/jupyterlab/jupyterlab/blob/4fc0a73336fe7bb92b2b2c0e6e8be89545086a50/packages/codeeditor/src/widget.ts#L51
//
//    Some method of the CodeMirror editor called when instantiating an editor in src/common/mergeview are also mocked.
//    As these tests are only checking the widget instantiation, it is fine.
jest.mock('@jupyterlab/codemirror', () => {
  return {
    CodeMirrorEditor: jest.fn(),
    CodeMirrorEditorFactory: jest.fn().mockImplementation(() => {
      return {
        newInlineEditor: jest.fn().mockImplementation((options: CodeEditor.IOptions) => {
          return {
            model: {
              selections: { changed: { connect: jest.fn() } },
            },
            editor: {
              getValue: jest.fn().mockImplementation(() => options.model.sharedModel),
              on: jest.fn(),
              operation: jest.fn(),
              state: {}
            },
          };
        }),
      };
    }),
  };
});

describe('merge', () => {

  describe('widget', () => {

    let rendermime = new RenderMimeRegistry({
      initialFactories: standardRendererFactories, sanitizer: defaultSanitizer});

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
          let model = new NotebookMergeModel(notebook, NBdecisions);
          let widget = new NotebookMergeWidget(model, rendermime);
          expect(widget).not.toBe(null);
          Widget.attach(widget, document.body);
      });

    });

  });

});
