// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.

import expect = require('expect.js');

import * as util from '../../../src/diff/util';

describe('diff', () => {

  describe('util', () => {

    describe('getDiffKey', () => {

      it('should return null for an empty diff', () => {
        let diff = util.getDiffKey([], 'not_present');
        expect(diff).to.be(null);
      });

    });

    
    describe('flattenStringDiff', () => {

       it('should work for an empty diff', () => {
        let diff = util.flattenStringDiff('test', []);
        expect(diff).to.eql([]);
      });

    });

  });

});
