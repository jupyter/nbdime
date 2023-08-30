// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.

globalThis.DragEvent = class DragEvent {} as any;

import { MergeView } from '../../../src/common/mergeview';
import { createDirectStringDiffModel } from '../../../src/diff/model/string';

// Mock codemirror editor as it is provided by JupyterLab
//  Note: the signal `selections.changed` must be mocked as it is connected
//    to a slot in CodeEditorWrapper in @jupyterlab/codeeditor (see
//    https://github.com/jupyterlab/jupyterlab/blob/4fc0a73336fe7bb92b2b2c0e6e8be89545086a50/packages/codeeditor/src/widget.ts#L51)
jest.mock('@jupyterlab/codemirror', () => {
  return {
    CodeMirrorEditor: jest.fn(),
    CodeMirrorEditorFactory: jest.fn().mockImplementation(() => {
      return {
        newInlineEditor: jest.fn().mockImplementation(() => {
          return {
            model: {
              selections: { changed: { connect: jest.fn() } },
            },
          };
        }),
      };
    }),
  };
});

describe('common', () => {
  describe('MergeView', () => {
    it('should be initialized for unchanged diff', () => {
      let orig = 'Value';
      let remote = createDirectStringDiffModel(orig, orig);
      let p = new MergeView({
        orig,
        remote,
      });
      expect(p).not.toBe(null);
    });
  });
});
