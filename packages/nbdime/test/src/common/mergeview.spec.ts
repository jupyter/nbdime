// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.

import { MergeView } from '../../../src/common/mergeview';
import { createDirectStringDiffModel } from '../../../src/diff/model/string';

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
