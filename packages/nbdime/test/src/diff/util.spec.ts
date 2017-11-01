// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.

import expect = require('expect.js');

import {
  deepCopy
} from '../../../src/common/util';

import * as util from '../../../src/diff/util';

import {
  opPatch, opAdd, opAddRange, opRemoveRange
} from '../../../src/diff/diffentries';

describe('diff', () => {

  describe('util', () => {

    describe('getSubDiffByKey', () => {

      it('should return null for an empty diff', () => {
        let diff = util.getSubDiffByKey([], 'not_present');
        expect(diff).to.be(null);
      });

      it('should return null for a null diff', () => {
        let diff = util.getSubDiffByKey(null, 'not_present');
        expect(diff).to.be(null);
      });

      it('should return null for a missing key', () => {
        let subdiff = [opAdd('foo', 11)];
        let diff = [opPatch('a', subdiff)];
        let value = util.getSubDiffByKey(diff, 'b');
        expect(value).to.be(null);
      });

      it('should return a sub-diff for valid key', () => {
        let subdiff = [opAdd('foo', 11)];
        let diff = [opPatch('a', subdiff)];
        let value = util.getSubDiffByKey(diff, 'a');
        expect(value).to.be(subdiff);
      });

      it('should return null for a key to a non-patch op', () => {
        let subdiff = [opAdd('foo', 11)];
        let diff = [opPatch('a', subdiff), opAdd('b', subdiff)];
        let value = util.getSubDiffByKey(diff, 'b');
        expect(value).to.be(null);
      });

    });


    describe('flattenStringDiff', () => {

      it('should work for an empty diff', () => {
        let diff = util.flattenStringDiff('test', []);
        expect(diff).to.eql([]);
      });

      it('should work for an empty diff on array of lines', () => {
        let diff = util.flattenStringDiff(['test'], []);
        expect(diff).to.eql([]);
      });

      it('should work for a valid line addition', () => {
        let source = ['test\n', 'foo\n', 'bar\n'];
        let sourceDiff = [
          opAddRange(1, ['wee\n'])
        ]
        let diff = util.flattenStringDiff(source, sourceDiff);
        let expected = [opAddRange(source[0].length, 'wee\n')];
        expect(util.stripSource(diff)).to.eql(expected);
      });

      it('should work for a valid line addition', () => {
        let source = ['test\n', 'foo\n', 'bar\n'];
        let sourceDiff = [
          opAddRange(1, ['wee\n'])
        ]
        let diff = util.flattenStringDiff(source, sourceDiff);
        let expected = [opAddRange(source[0].length, 'wee\n')];
        expect(util.stripSource(diff)).to.eql(expected);
      });

      it('should combine subsequent line additions', () => {
        let source = ['test\n', 'foo\n', 'bar\n'];
        let sourceDiff = [
          opAddRange(1, ['wee\n']),
          opAddRange(1, ['ooh\n'])
        ]
        let diff = util.flattenStringDiff(source, sourceDiff);
        let expected = [opAddRange(source[0].length, 'wee\nooh\n')];
        expect(util.stripSource(diff)).to.eql(expected);
      });

      it('should be robust against different line endings', () => {
        let sourceA = 'test\nfoo\n\nbar\n';
        let sourceB = sourceA.replace(/\n/gm, '\r\n');
        let sourceC = sourceA.replace(/\n/gm, '\r');
        let sourceDiffA = [
          opAddRange(3, ['wee\n']),
          opAddRange(3, ['ooh\n'])
        ]
        let sourceDiffB = deepCopy(sourceDiffA);
        (sourceDiffB[0].valuelist as string[])[0] = sourceDiffA[0].valuelist[0].replace(/\n/gm, '\r\n');
        (sourceDiffB[1].valuelist as string[])[0] = sourceDiffA[1].valuelist[0].replace(/\n/gm, '\r\n');
        let sourceDiffC = deepCopy(sourceDiffA);
        (sourceDiffC[0].valuelist as string[])[0] = sourceDiffA[0].valuelist[0].replace(/\n/gm, '\r');
        (sourceDiffC[1].valuelist as string[])[0] = sourceDiffA[1].valuelist[0].replace(/\n/gm, '\r');

        let diff = util.flattenStringDiff(sourceA, sourceDiffA);
        let expected = [opAddRange('test\nfoo\n\n'.length, 'wee\nooh\n')];
        expect(util.stripSource(diff)).to.eql(expected);

        diff = util.flattenStringDiff(sourceB, sourceDiffB);
        expected = [opAddRange('test\r\nfoo\r\n\r\n'.length, 'wee\r\nooh\r\n')];
        expect(util.stripSource(diff)).to.eql(expected);

        diff = util.flattenStringDiff(sourceC, sourceDiffC);
        expected = [opAddRange('test\rfoo\r\r'.length, 'wee\rooh\r')];
        expect(util.stripSource(diff)).to.eql(expected);
      });

      it('should work for a valid line deletion', () => {
        let source = ['test\n', 'foo\n', 'bar\n'];
        let sourceDiff = [
          opRemoveRange(1, 1)
        ]
        let diff = util.flattenStringDiff(source, sourceDiff);
        let expected = [opRemoveRange(source[0].length, 'wee\n'.length)];
        expect(util.stripSource(diff)).to.eql(expected);
      });

      it('should combine subsequent line deletions', () => {
        let source = ['test\n', 'foo\n', 'bar\n'];
        let sourceDiff = [
          opRemoveRange(1, 1),
          opRemoveRange(2, 1)
        ];
        let diff = util.flattenStringDiff(source, sourceDiff);
        let expected = [opRemoveRange(source[0].length, 'foo\nbar\n'.length)];
        expect(util.stripSource(diff)).to.eql(expected);
      });

    });

  });

});
