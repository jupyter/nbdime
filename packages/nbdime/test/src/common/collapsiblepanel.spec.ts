// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.

import {
  Widget
} from '@lumino/widgets';

import {
    CollapsiblePanel
} from '../../../src/common/collapsiblepanel';

describe('common', () => {

  describe('CollapsiblePanel', () => {

    it('should be initialized with an inner widget', () => {
      let inner = new Widget();
      let p = new CollapsiblePanel(inner);
      expect(p).not.toBe(null);
    });

  });

});
