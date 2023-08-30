// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.

globalThis.DragEvent = class DragEvent {} as any;

import type * as nbformat from '@jupyterlab/nbformat';

import {
  RenderMimeRegistry, standardRendererFactories
} from '@jupyterlab/rendermime';

import {
    OutputDiffModel
} from '../../../../src/diff/model/output';

import {
    OutputPanel
} from '../../../../src/diff/widget/output';


describe('diff', () => {

  describe('widget', () => {

    describe('OutputPanel', () => {

      describe('#isTrustSignificant', () => {

        let rendermime = new RenderMimeRegistry({initialFactories: standardRendererFactories});

        let model: OutputDiffModel;
        let base: nbformat.IExecuteResult;
        let remote: nbformat.IDisplayData;
        beforeEach(() => {
          base = {
              output_type: 'execute_result',
              data: {},
              execution_count: 4,
              metadata: {}
            };
          remote = {
              output_type: 'display_data',
              data: {},
              metadata: {}
            };
          model = new OutputDiffModel(base, remote);
        });

        it('should say insignificant for plain text', () => {
          base.data['text/plain'] = '365.0';
          let significant = OutputPanel.isTrustSignificant(model, rendermime);
          expect(significant).toBe(false);
        });

        it('should say insignificant for plain text in remote', () => {
          remote.data['text/plain'] = '365.0';
          let significant = OutputPanel.isTrustSignificant(model, rendermime);
          expect(significant).toBe(false);
        });

        it('should say significant for untrusted html', () => {
          base.data['text/html'] = '<html><body><script>alert("wee");</script></body></html';
          let significant = OutputPanel.isTrustSignificant(model, rendermime);
          expect(significant).toBe(true);
        });

        it('should say significant for untrusted html in remote', () => {
          remote.data['text/html'] = '<html><body><script>alert("wee");</script></body></html';
          let significant = OutputPanel.isTrustSignificant(model, rendermime);
          expect(significant).toBe(true);
        });

        it('should say insignificant for trusted html', () => {
          base.data['text/html'] = '<html><body><script>alert("wee");</script></body></html';
          model.trusted = true;
          let significant = OutputPanel.isTrustSignificant(model, rendermime);
          expect(significant).toBe(false);
        });

      });

    });

  });

});
