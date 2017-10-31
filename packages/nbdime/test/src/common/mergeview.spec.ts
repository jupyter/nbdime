// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.

import expect = require('expect.js');

import {
  createDirectStringDiffModel
} from '../../../src/diff/model/string';

import {
  MergeView, createNbdimeMergeView
} from '../../../src/common/mergeview';


describe('common', () => {

  describe('MergeView', () => {

    it('should be initialized for unchanged diff', () => {
      let orig = 'Value';
      let remote = createDirectStringDiffModel(orig, orig);
      let p = new MergeView({
        orig,
        remote
      });
      expect(p).to.not.be(null);
    });

  });

});
