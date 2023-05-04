// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.

import { DragDropPanel } from '../../../src/common/dragpanel';

describe('common', () => {
  describe('DragPanel', () => {
    it('should be initialized with no options', () => {
      let p = new DragDropPanel();
      expect(p).not.toBe(null);
    });
  });
});
