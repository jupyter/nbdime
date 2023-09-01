// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.

import { MergeView } from '../../../src/common/mergeview';
import { createDirectStringDiffModel } from '../../../src/diff/model/string';

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
