// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.

import expect = require('expect.js');

import {
    FlexPanel
} from '../../../src/upstreaming/flexpanel';


describe('upstreaming', () => {

  describe('FlexPanel', () => {

    it('should be initialized with no options', () => {
      let p = new FlexPanel();
      expect(p).to.not.be(null);
    });

  });

});
