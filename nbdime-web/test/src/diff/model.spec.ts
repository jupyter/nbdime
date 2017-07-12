// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.

import expect = require('expect.js');

import {
  nbformat
} from '@jupyterlab/coreutils';

import {
  JSONValue
} from '@phosphor/coreutils';

import {
  createAddedCellDiffModel, createDeletedCellDiffModel,
  createPatchedCellDiffModel, createUnchangedCellDiffModel
} from '../../../src/diff/model/cell';

import {
  NotebookDiffModel
} from '../../../src/diff/model/notebook';

import {
  OutputDiffModel
} from '../../../src/diff/model/output';

import {
  createPatchStringDiffModel, createDirectStringDiffModel,
} from '../../../src/diff/model/string';

import {
  opAddRange, opPatch, IDiffEntry
} from '../../../src/diff/diffentries';

import {
  stringify
} from '../../../src/patch';


describe('diff', () => {

  describe('model', () => {

    // Note: Chunking is covered in chunking.spec.ts

    describe('createDirectStringDiffModel', () => {

      it('should create an added model', () => {
          let model = createDirectStringDiffModel(null, 'foobar!');
          expect(model.added).to.be(true);
          expect(model.deleted).to.be(false);
          expect(model.unchanged).to.be(false);
          expect(model.additions).to.not.be.empty();
          expect(model.deletions).to.be.empty();
      });

      it('should create a deleted model', () => {
          let model = createDirectStringDiffModel('foobar!', null);
          expect(model.added).to.be(false);
          expect(model.deleted).to.be(true);
          expect(model.unchanged).to.be(false);
          expect(model.additions).to.be.empty();
          expect(model.deletions).to.not.be.empty();
      });

      it('should create an unchanged model', () => {
          let model = createDirectStringDiffModel('foobar!', 'foobar!');
          expect(model.added).to.be(false);
          expect(model.deleted).to.be(false);
          expect(model.unchanged).to.be(true);
          expect(model.additions).to.be.empty();
          expect(model.deletions).to.be.empty();
      });

      it('should fail for differing non-null string inputs', () => {
          expect(createDirectStringDiffModel).withArgs(
              'foobar!', 'barfoo!').to.throwException(
                  /Invalid arguments to createDirectStringDiffModel\(\)/
              );
      });

      it('should fail for all null inputs', () => {
          expect(createDirectStringDiffModel).withArgs(
              null, null).to.throwException(
                  /Invalid arguments to createDirectStringDiffModel\(\)/
              );
      });

    });

    describe('createPatchStringDiffModel', () => {

      // Note: Patching is covered inn patch/patching.spec.ts

      it('should create a patched model', () => {
          let base = [0, 1, 'foo'];
          let diff = [opAddRange(2, 'bar')];
          let model = createPatchStringDiffModel(base, diff);
          expect(model.added).to.be(false);
          expect(model.deleted).to.be(false);
          expect(model.unchanged).to.be(false);
          expect(model.additions).to.not.be.empty();
          expect(model.deletions).to.be.empty();
      });

      it('should create an unchanged model by empty diff', () => {
          let base = 'foobar!';
          let diff: IDiffEntry[] = [];
          let model = createPatchStringDiffModel(base, diff);
          expect(model.added).to.be(false);
          expect(model.deleted).to.be(false);
          expect(model.unchanged).to.be(true);
          expect(model.additions).to.be.empty();
          expect(model.deletions).to.be.empty();
      });

      it('should create an unchanged model by empty diff for non-string input', () => {
          let base = [0, 1, 'foo'];
          let diff: IDiffEntry[] = [];
          let model = createPatchStringDiffModel(base, diff);
          expect(model.added).to.be(false);
          expect(model.deleted).to.be(false);
          expect(model.unchanged).to.be(true);
          expect(model.additions).to.be.empty();
          expect(model.deletions).to.be.empty();
      });

    });

    describe('OutputDiffModel', () => {

      let dummyOutput: nbformat.IStream = {
        output_type: 'stream',
        name: 'stdout',
        text: 'Foo!'
      };

      it('should create an added model', () => {
        let model = new OutputDiffModel(
          null, dummyOutput
        );
        expect(model.added).to.be(true);
        expect(model.deleted).to.be(false);
        expect(model.unchanged).to.be(false);
      });

      it('should create a deleted model', () => {
        let model = new OutputDiffModel(
          dummyOutput, null
        );
        expect(model.added).to.be(false);
        expect(model.deleted).to.be(true);
        expect(model.unchanged).to.be(false);
      });

      it('should create an unchanged model', () => {
        let model = new OutputDiffModel(
            dummyOutput, dummyOutput
        );
        expect(model.added).to.be(false);
        expect(model.deleted).to.be(false);
        expect(model.unchanged).to.be(true);
      });

      it('should patch output if given diff and no remote', () => {
        let diff = [opPatch('text', [opPatch(0, [opAddRange(3, ' bar')])])];
        let model = new OutputDiffModel(dummyOutput, null, diff);
        expect(model.added).to.be(false);
        expect(model.deleted).to.be(false);
        expect(model.unchanged).to.be(false);
        expect(model.diff).to.be(diff);
        expect(model.remote).to.eql({
          output_type: 'stream',
          name: 'stdout',
          text: 'Foo bar!'
        });
      });

      it('should fail for all null input', () => {
        expect(() => {
          new OutputDiffModel(null, null );
        }).to.throwException(
          /Either remote or base value need to be given/);
      });

    });

    describe('CellDiffModel', () => {

      let codeCellA: nbformat.ICodeCell = {
        'cell_type': 'code',
        'execution_count': 2,
        'metadata': {
          'collapsed': false,
          'trusted': false
        },
        'outputs': [
        ],
        'source':
          'l = f(3, 4)\nprint(l)'
      };
      let mimetype = 'text/python';

      it('should be creatable by createAddedCellDiffModel', () => {
        let model = createAddedCellDiffModel(codeCellA, mimetype);
        expect(model.added).to.be(true);
        expect(model.deleted).to.be(false);
        expect(model.unchanged).to.be(false);
        expect(model.source.base).to.be(null);
        expect(model.source.remote).to.eql(codeCellA.source);
        expect(model.metadata.base).to.be(null);
        expect(model.metadata.remote).to.eql(stringify(codeCellA.metadata as JSONValue));
        expect(model.outputs!.length).to.equal(codeCellA.outputs.length);
      });

      it('should be creatable by createDeletedCellDiffModel', () => {
        let model = createDeletedCellDiffModel(codeCellA, mimetype);
        expect(model.added).to.be(false);
        expect(model.deleted).to.be(true);
        expect(model.unchanged).to.be(false);
        expect(model.source.base).to.eql(codeCellA.source);
        expect(model.source.remote).to.be(null);
        expect(model.metadata.base).to.eql(stringify(codeCellA.metadata as JSONValue));
        expect(model.metadata.remote).to.be(null);
        expect(model.outputs!.length).to.equal(codeCellA.outputs.length);
      });

      it('should be creatable by createUnchangedCellDiffModel', () => {
        let model = createUnchangedCellDiffModel(codeCellA, mimetype);
        expect(model.added).to.be(false);
        expect(model.deleted).to.be(false);
        expect(model.unchanged).to.be(true);
        expect(model.source.base).to.eql(codeCellA.source);
        expect(model.source.remote).to.eql(codeCellA.source);
        expect(model.metadata.base).to.eql(stringify(codeCellA.metadata as JSONValue));
        expect(model.metadata.remote).to.eql(stringify(codeCellA.metadata as JSONValue));
        expect(model.outputs!.length).to.equal(codeCellA.outputs.length);
      });

      describe('createPatchedCellDiffModel', () => {

        it('should create an unchanged model for null diff', () => {
          let model = createPatchedCellDiffModel(codeCellA, null, mimetype);
          expect(model.added).to.be(false);
          expect(model.deleted).to.be(false);
          expect(model.unchanged).to.be(true);
          expect(model.source.base).to.eql(codeCellA.source);
          expect(model.source.remote).to.eql(codeCellA.source);
          expect(model.metadata.base).to.eql(stringify(codeCellA.metadata as JSONValue));
          expect(model.metadata.remote).to.eql(stringify(codeCellA.metadata as JSONValue));
          expect(model.outputs!.length).to.equal(codeCellA.outputs.length);
        });

        it('should create an unchanged model for an empty diff', () => {
          let model = createPatchedCellDiffModel(codeCellA, [], mimetype);
          expect(model.added).to.be(false);
          expect(model.deleted).to.be(false);
          expect(model.unchanged).to.be(true);
          expect(model.source.base).to.eql(codeCellA.source);
          expect(model.source.remote).to.eql(codeCellA.source);
          expect(model.metadata.base).to.eql(stringify(codeCellA.metadata as JSONValue));
          expect(model.metadata.remote).to.eql(stringify(codeCellA.metadata as JSONValue));
          expect(model.outputs!.length).to.equal(codeCellA.outputs.length);
        });

        it('should create a patched model with a diff', () => {
          let diff = [
            opPatch('source', [opAddRange(1, ['l += 2\n'])])
          ];
          let model = createPatchedCellDiffModel(codeCellA, diff, mimetype);
          expect(model.added).to.be(false);
          expect(model.deleted).to.be(false);
          expect(model.unchanged).to.be(false);
          expect(model.source.base).to.eql(codeCellA.source);
          expect(model.source.remote).to.eql('l = f(3, 4)\nl += 2\nprint(l)');
          expect(model.metadata.base).to.eql(stringify(codeCellA.metadata as JSONValue));
          expect(model.metadata.remote).to.eql(stringify(codeCellA.metadata as JSONValue));
          expect(model.outputs!.length).to.equal(codeCellA.outputs.length);
        });

      });

    });

    describe('NotebookDiffModel', () => {
    });

  });

});
