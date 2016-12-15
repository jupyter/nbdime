// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
'use strict';

import expect = require('expect.js');

import {
  notebookStub, codeCellStub
} from '../testutil';

import {
  stripSource
} from '../../../src/diff/util';

import {
  shallowCopy
} from '../../../src/common/util';

import {
  opPatch, opAddRange, opRemoveRange, IDiffAddRange,
  IDiffRemoveRange, IDiffPatchArray
} from '../../../src/diff/diffentries';

import {
  createPatchStringDiffModel, IStringDiffModel
} from '../../../src/diff/model';

import {
  IMergeDecision
} from '../../../src/merge/decisions';

import {
  NotebookMergeModel
} from '../../../src/merge/model';

import {
  updateModel
} from '../../../src/merge/manualedit';





describe('merge', () => {

  describe('updateModel', () => {

    describe('unchanged cell', () => {

      it('should update a simple line insertion', () => {
        let nbcontent = shallowCopy(notebookStub);
        let cell = shallowCopy(codeCellStub);
        cell.source = 'abcdef\njkl\n';
        nbcontent.cells = [cell];
        let nbmodel = new NotebookMergeModel(nbcontent, []);
        let model = nbmodel.cells[0].merged.source;
        updateModel({
          model: model,
          fullLines: ['abcdef\n', 'ghi\n', 'jkl\n', ''],
          baseLine: 1,
          editLine: 1,
          editCh: 0,
          oldval: [''],
          newval: ['ghi', '']
        });
        expect(model.remote).to.be('abcdef\nghi\njkl\n');
        expect(nbmodel.cells[0].deleteCell).to.be(false);
        expect(nbmodel.cells[0].decisions.length).to.be(1);
        expect(nbmodel.cells[0].decisions[0].absolutePath).to.eql(['cells', 0, 'source']);
        let diff = stripSource(nbmodel.cells[0].decisions[0].customDiff)!;
        expect(diff).to.eql([
          opAddRange(1, ['ghi\n'])
        ]);
      });

      it('should update a simple line deletion', () => {
        let nbcontent = shallowCopy(notebookStub);
        let cell = shallowCopy(codeCellStub);
        cell.source = 'abcdef\njkl\n';
        nbcontent.cells = [cell];
        let nbmodel = new NotebookMergeModel(nbcontent, []);
        let model = nbmodel.cells[0].merged.source;
        updateModel({
          model: model,
          fullLines: ['abcdef\n', ''],
          baseLine: 1,
          editLine: 1,
          editCh: 0,
          oldval: ['jkl', ''],
          newval: ['']
        });
        expect(model.remote).to.be('abcdef\n');
        expect(model.additions).to.be.empty();
        expect(model.deletions.length).to.be(1);
        expect(nbmodel.cells[0].decisions.length).to.be(1);
        expect(nbmodel.cells[0].decisions[0].absolutePath).to.eql(['cells', 0, 'source']);
        let diff = stripSource(nbmodel.cells[0].decisions[0].customDiff)!;
        expect(diff).to.eql([
          opRemoveRange(1, 1)
        ]);
      });

    });


    describe('inserted cell', () => {

      it('should update a simple line addition', () => {
        let cell = shallowCopy(codeCellStub);
        cell.source = 'abcdef\njkl\n';
        let decisions: IMergeDecision[] = [{
          'common_path': ['cells'],
          'local_diff': [opAddRange(0, [cell])],
          'action': 'local'
        }];
        let nbmodel = new NotebookMergeModel(notebookStub, decisions);
        let model = nbmodel.cells[0].merged.source;
        updateModel({
          model: model,
          fullLines: ['abcdef\n', 'ghi\n', 'jkl\n', ''],
          baseLine: 1,
          editLine: 1,
          editCh: 0,
          oldval: [''],
          newval: ['ghi', '']
        });
        let expectedCell = shallowCopy(codeCellStub);
        expectedCell.source = 'abcdef\nghi\njkl\n';
        expect(model.remote).to.be(expectedCell.source);
        let diff = stripSource(nbmodel.cells[0].decisions[0].customDiff)!;
        expect((diff[0] as IDiffAddRange).valuelist[0]).to.eql(expectedCell);
        expect(model.deletions).to.be.empty();
        expect(model.additions.length).to.be(1);
        expect(model.additions[0].from).to.eql({line: 0, ch: 0});
        expect(model.additions[0].to).to.eql({line: 3, ch: 0});
        expect(nbmodel.cells[0].decisions.length).to.be(1);
        expect(nbmodel.cells[0].decisions[0].absolutePath).to.eql(['cells']);
      });

      it('should update a simple character addition', () => {
        let cell = shallowCopy(codeCellStub);
        cell.source = 'abcdef\ngh\njkl\n';
        let decisions: IMergeDecision[] = [{
          'common_path': ['cells'],
          'local_diff': [opAddRange(0, [cell])],
          'action': 'local'
        }];
        let nbmodel = new NotebookMergeModel(notebookStub, decisions);
        let model = nbmodel.cells[0].merged.source;
        updateModel({
          model: model,
          fullLines: ['abcdef\n', 'ghi\n', 'jkl\n', ''],
          baseLine: 1,
          editLine: 1,
          editCh: 0,
          oldval: [''],
          newval: ['i']
        });
        let expectedCell = shallowCopy(codeCellStub);
        expectedCell.source = 'abcdef\nghi\njkl\n';
        expect(model.remote).to.be(expectedCell.source);
        let diff = stripSource(nbmodel.cells[0].decisions[0].customDiff)!;
        expect((diff[0] as IDiffAddRange).valuelist[0]).to.eql(expectedCell);
        expect(nbmodel.cells[0].decisions.length).to.be(1);
        expect(nbmodel.cells[0].decisions[0].absolutePath).to.eql(['cells']);
      });

      it('should update a simple line deletion', () => {
        let cell = shallowCopy(codeCellStub);
        cell.source = 'abcdef\njkl\n';
        let decisions: IMergeDecision[] = [{
          'common_path': ['cells'],
          'local_diff': [opAddRange(0, [cell])],
          'action': 'local'
        }];
        let nbmodel = new NotebookMergeModel(notebookStub, decisions);
        let model = nbmodel.cells[0].merged.source;
        updateModel({
          model: model,
          fullLines: ['abcdef\n', ''],
          baseLine: 1,
          editLine: 1,
          editCh: 0,
          oldval: ['jkl', ''],
          newval: ['']
        });
        let expectedCell = shallowCopy(codeCellStub);
        expectedCell.source = 'abcdef\n';
        expect(model.remote).to.be(expectedCell.source);
        let diff = stripSource(nbmodel.cells[0].decisions[0].customDiff)!;
        expect((diff[0] as IDiffAddRange).valuelist[0]).to.eql(expectedCell);
        expect(nbmodel.cells[0].decisions.length).to.be(1);
        expect(nbmodel.cells[0].decisions[0].absolutePath).to.eql(['cells']);
      });

      it('should update a simple character deletion', () => {
        let cell = shallowCopy(codeCellStub);
        cell.source = 'abcdef\nghi\njkl\n';
        let decisions: IMergeDecision[] = [{
          'common_path': ['cells'],
          'local_diff': [opAddRange(0, [cell])],
          'action': 'local'
        }];
        let nbmodel = new NotebookMergeModel(notebookStub, decisions);
        let model = nbmodel.cells[0].merged.source;
        updateModel({
          model: model,
          fullLines: ['abcdef\n', 'gh\n', 'jkl\n', ''],
          baseLine: 1,
          editLine: 1,
          editCh: 0,
          oldval: ['i'],
          newval: ['']
        });
        let expectedCell = shallowCopy(codeCellStub);
        expectedCell.source = 'abcdef\ngh\njkl\n';
        expect(model.remote).to.be(expectedCell.source);
        let diff = stripSource(nbmodel.cells[0].decisions[0].customDiff)!;
        expect((diff[0] as IDiffAddRange).valuelist[0]).to.eql(expectedCell);
        expect(nbmodel.cells[0].decisions.length).to.be(1);
        expect(nbmodel.cells[0].decisions[0].absolutePath).to.eql(['cells']);
      });

      it('should update a two subsequent line deletions', () => {
        let cell = shallowCopy(codeCellStub);
        cell.source = 'abcdef\njkl\nmnp\n';
        let decisions: IMergeDecision[] = [{
          'common_path': ['cells'],
          'remote_diff': [opAddRange(0, [cell])],
          'action': 'local'
        }];
        let nbmodel = new NotebookMergeModel(notebookStub, decisions);
        let model = nbmodel.cells[0].merged.source;
        updateModel({
          model: model,
          fullLines: ['abcdef\n', 'mnp\n', ''],
          baseLine: 1,
          editLine: 1,
          editCh: 0,
          oldval: ['jkl', ''],
          newval: ['']
        });
        updateModel({
          model: model,
          fullLines: ['abcdef\n', ''],
          baseLine: 1,
          editLine: 1,
          editCh: 0,
          oldval: ['mnp', ''],
          newval: ['']
        });
        let expectedCell = shallowCopy(codeCellStub);
        expectedCell.source = 'abcdef\n';
        expect(model.remote).to.be(expectedCell.source);
        let diff = stripSource(nbmodel.cells[0].decisions[0].customDiff)!;
        expect((diff[0] as IDiffAddRange).valuelist[0]).to.eql(expectedCell);
        expect(nbmodel.cells[0].decisions.length).to.be(1);
        expect(nbmodel.cells[0].decisions[0].absolutePath).to.eql(['cells']);
      });

      it('should update a simple line replacement', () => {
        let cell = shallowCopy(codeCellStub);
        cell.source = 'abcdef\njkl\n';
        let decisions: IMergeDecision[] = [{
          'common_path': ['cells'],
          'local_diff': [opAddRange(0, [cell])],
          'action': 'local'
        }];
        let nbmodel = new NotebookMergeModel(notebookStub, decisions);
        let model = nbmodel.cells[0].merged.source;
        updateModel({
          model: model,
          fullLines: ['abcdef\n', 'ghi\n', ''],
          baseLine: 1,
          editLine: 1,
          editCh: 0,
          oldval: ['jkl', ''],
          newval: ['ghi', '']
        });
        let expectedCell = shallowCopy(codeCellStub);
        expectedCell.source = 'abcdef\nghi\n';
        expect(model.remote).to.be(expectedCell.source);
        let diff = stripSource(nbmodel.cells[0].decisions[0].customDiff)!;
        expect((diff[0] as IDiffAddRange).valuelist[0]).to.eql(expectedCell);
        expect(nbmodel.cells[0].decisions.length).to.be(1);
        expect(nbmodel.cells[0].decisions[0].absolutePath).to.eql(['cells']);
      });

    });


    describe('deleted cell', () => {

      it('should update a simple line addition', () => {
        let nbcontent = shallowCopy(notebookStub);
        let cell = shallowCopy(codeCellStub);
        cell.source = 'abcdef\njkl\n';
        nbcontent.cells = [cell];
        let decisions: IMergeDecision[] = [{
          'common_path': ['cells'],
          'local_diff': [opRemoveRange(0, 1)],
          'action': 'local'
        }];
        let nbmodel = new NotebookMergeModel(nbcontent, decisions);
        let model = nbmodel.cells[0].merged.source;
        updateModel({
          model: model,
          fullLines: ['abcdef\n', 'ghi\n', 'jkl\n', ''],
          baseLine: 1,
          editLine: 1,
          editCh: 0,
          oldval: [''],
          newval: ['ghi', '']
        });
        let expectedCell = shallowCopy(codeCellStub);
        expectedCell.source = 'abcdef\nghi\njkl\n';
        expect(model.remote).to.be(expectedCell.source);
        expect(nbmodel.cells[0].deleteCell).to.be(false);
        expect(nbmodel.cells[0].decisions.length).to.be(1);
        expect(nbmodel.cells[0].decisions[0].absolutePath).to.eql(['cells']);
        let diff = stripSource(nbmodel.cells[0].decisions[0].customDiff)!;
        diff = (diff[0] as IDiffPatchArray).diff!;
        diff = (diff[0] as IDiffPatchArray).diff!;
        expect(diff).to.eql([
          opAddRange(1, ['ghi\n'])
        ]);
      });

      it('should update a simple line deletion', () => {
        let nbcontent = shallowCopy(notebookStub);
        let cell = shallowCopy(codeCellStub);
        cell.source = 'abcdef\nghi\njkl\n';
        nbcontent.cells = [cell];
        let decisions: IMergeDecision[] = [{
          'common_path': ['cells'],
          'local_diff': [opRemoveRange(0, 1)],
          'action': 'local'
        }];
        let nbmodel = new NotebookMergeModel(nbcontent, decisions);
        let model = nbmodel.cells[0].merged.source;
        updateModel({
          model: model,
          fullLines: ['abcdef\n', 'jkl\n', ''],
          baseLine: 1,
          editLine: 1,
          editCh: 0,
          oldval: ['ghi', ''],
          newval: ['']
        });
        expect(model.remote).to.be('abcdef\njkl\n');
        let diff = stripSource(nbmodel.cells[0].decisions[0].customDiff)!;
        diff = (diff[0] as IDiffPatchArray).diff!;
        diff = (diff[0] as IDiffPatchArray).diff!;
        expect(diff[0]).to.eql(opRemoveRange(1, 1));
        expect(nbmodel.cells[0].deleteCell).to.be(false);
        expect(nbmodel.cells[0].decisions.length).to.be(1);
        expect(nbmodel.cells[0].decisions[0].absolutePath).to.eql(['cells']);
      });

      it('should update a deletion on a previously edited model', () => {
        // This test adds an initial custom diff, whose changes are
        // subsequently all deleted
        let nbcontent = shallowCopy(notebookStub);
        let cell = shallowCopy(codeCellStub);
        cell.source = 'abcdef\njkl\nmnpq\nuv\n';
        nbcontent.cells = [cell];
        // Set up initial deleted cell model
        let decisions: IMergeDecision[] = [{
          common_path: ['cells'],
          local_diff: [opRemoveRange(0, 1)],
          action: 'local'
        }];
        let nbmodel = new NotebookMergeModel(nbcontent, decisions);
        let cellModel = nbmodel.cells[0];
        // Simulate diff after previous manual edit
        let dec = cellModel.decisions[0];
        dec.customDiff = [opPatch(0, [opPatch('source', [
            opAddRange(1, ['ghi\n']),
            opRemoveRange(1, 1),
            opPatch(2, [
              opAddRange(2, 'o'),
              opRemoveRange(2, 1)
            ]),
            opAddRange(3, ['rst\n'])
          ])])];
        dec.action = 'custom';
        // Perform new edit:
        let model = cellModel.merged.source;
        // Value at this point:
        // 'abcdef\nghi\nmnoq\nrst\nuv\n'
        updateModel({
          model: model,
          fullLines: ['abcv\n', ''],
          baseLine: 0,
          editLine: 0,
          editCh: 3,
          oldval: ['def', 'ghi', 'mnoq', 'rst', 'u'],
          newval: ['']
        });
        expect(model.remote).to.be('abcv\n');
        let diff = stripSource(nbmodel.cells[0].decisions[0].customDiff)!;
        diff = (diff[0] as IDiffPatchArray).diff!;
        diff = (diff[0] as IDiffPatchArray).diff!;
        expect(diff).to.eql([
          opAddRange(0, ['abcv\n']),
          opRemoveRange(0, 5)
          ]);
        expect(nbmodel.cells[0].deleteCell).to.be(false);
        expect(nbmodel.cells[0].decisions.length).to.be(1);
        expect(nbmodel.cells[0].decisions[0].absolutePath).to.eql(['cells']);
      });

      it('should update a partial deletion on a previously edited model', () => {
        // This test adds an initial custom diff, whose changes are
        // subsequently partially deleted
        let nbcontent = shallowCopy(notebookStub);
        let cell = shallowCopy(codeCellStub);
        cell.source = 'abcdef\njkl\nmnpq\nuv\n';
        nbcontent.cells = [cell];
        // Set up initial deleted cell model
        let decisions: IMergeDecision[] = [{
          common_path: ['cells'],
          local_diff: [opRemoveRange(0, 1)],
          action: 'local'
        }];
        let nbmodel = new NotebookMergeModel(nbcontent, decisions);
        let cellModel = nbmodel.cells[0];
        // Simulate diff after previous manual edit
        let dec = cellModel.decisions[0];
        dec.customDiff = [opPatch(0, [opPatch('source', [
            opAddRange(1, ['ghi\n']),
            opRemoveRange(1, 1),
            opPatch(2, [
              opAddRange(2, 'o'),
              opRemoveRange(2, 1)
            ]),
            opAddRange(3, ['rst\n'])
          ])])];
        dec.action = 'custom';
        // Perform new edit:
        let model = cellModel.merged.source;
        updateModel({
          model: model,
          fullLines: ['abcdef\n', 'ghq\n', 'rst\n', 'uv\n', ''],
          baseLine: 1,
          editLine: 1,
          editCh: 2,
          oldval: ['i', 'mno'],
          newval: ['']
        });
        expect(model.remote).to.be('abcdef\nghq\nrst\nuv\n');
        let diff = stripSource(nbmodel.cells[0].decisions[0].customDiff)!;
        diff = (diff[0] as IDiffPatchArray).diff!;
        diff = (diff[0] as IDiffPatchArray).diff!;
        expect(diff).to.eql([
          opAddRange(1, ['ghq\n']),
          opRemoveRange(1, 2),
          opAddRange(3, ['rst\n'])
          ]);
        expect(nbmodel.cells[0].deleteCell).to.be(false);
        expect(nbmodel.cells[0].decisions.length).to.be(1);
        expect(nbmodel.cells[0].decisions[0].absolutePath).to.eql(['cells']);
      });

      it('should handle two subsequent insertions', () => {
        let nbcontent = shallowCopy(notebookStub);
        let cell = shallowCopy(codeCellStub);
        cell.source = 'abcdef\njkl\n';
        nbcontent.cells = [cell];
        let decisions: IMergeDecision[] = [{
          'common_path': ['cells'],
          'local_diff': [opRemoveRange(0, 1)],
          'action': 'local'
        }];
        let nbmodel = new NotebookMergeModel(nbcontent, decisions);
        let model = nbmodel.cells[0].merged.source;
        updateModel({
          model: model,
          fullLines: ['abcdef\n', 'ghi\n', 'jkl\n', ''],
          baseLine: 1,
          editLine: 1,
          editCh: 0,
          oldval: [''],
          newval: ['ghi', '']
        });
        updateModel({
          model: model,
          fullLines: ['abcdef\n', 'ghi\n', 'xyz\n', 'jkl\n', ''],
          baseLine: 1,
          editLine: 2,
          editCh: 0,
          oldval: [''],
          newval: ['xyz', '']
        });
        let expectedCell = shallowCopy(codeCellStub);
        expectedCell.source = 'abcdef\nghi\nxyz\njkl\n';
        expect(model.remote).to.be(expectedCell.source);
        let diff = stripSource(nbmodel.cells[0].decisions[0].customDiff)!;
        diff = (diff[0] as IDiffPatchArray).diff!;
        diff = (diff[0] as IDiffPatchArray).diff!;
        expect(diff).to.eql([
          opAddRange(1, ['ghi\n', 'xyz\n'])
        ]);
        expect(nbmodel.cells[0].deleteCell).to.be(false);
        expect(nbmodel.cells[0].decisions.length).to.be(1);
        expect(nbmodel.cells[0].decisions[0].absolutePath).to.eql(['cells']);
      });

      it('should handle a newline insertion at end of line', () => {
        let nbcontent = shallowCopy(notebookStub);
        let cell = shallowCopy(codeCellStub);
        cell.source = 'abcdef\njkl\n';
        nbcontent.cells = [cell];
        let decisions: IMergeDecision[] = [{
          'common_path': ['cells'],
          'local_diff': [opRemoveRange(0, 1)],
          'action': 'local'
        }];
        let nbmodel = new NotebookMergeModel(nbcontent, decisions);
        let model = nbmodel.cells[0].merged.source;
        updateModel({
          model: model,
          fullLines: ['abcdef\n', '\n', 'jkl\n', ''],
          baseLine: 0,
          editLine: 0,
          editCh: 6,
          oldval: [''],
          newval: ['', '']
        });
        let expectedCell = shallowCopy(codeCellStub);
        expectedCell.source = 'abcdef\n\njkl\n';
        expect(model.remote).to.be(expectedCell.source);
        let diff = stripSource(nbmodel.cells[0].decisions[0].customDiff)!;
        diff = (diff[0] as IDiffPatchArray).diff!;
        diff = (diff[0] as IDiffPatchArray).diff!;
        // Ideal: [opAddRange(1, ['\n'])]
        expect(diff).to.eql([
          opAddRange(0, ['abcdef\n', '\n']),
          opRemoveRange(0, 1)
        ]);
        expect(nbmodel.cells[0].deleteCell).to.be(false);
        expect(nbmodel.cells[0].decisions.length).to.be(1);
        expect(nbmodel.cells[0].decisions[0].absolutePath).to.eql(['cells']);
      });

      it('should handle a newline insertion in the middle of a line', () => {
        let nbcontent = shallowCopy(notebookStub);
        let cell = shallowCopy(codeCellStub);
        cell.source = 'abcdef\njkl\n';
        nbcontent.cells = [cell];
        let decisions: IMergeDecision[] = [{
          'common_path': ['cells'],
          'local_diff': [opRemoveRange(0, 1)],
          'action': 'local'
        }];
        let nbmodel = new NotebookMergeModel(nbcontent, decisions);
        let model = nbmodel.cells[0].merged.source;
        updateModel({
          model: model,
          fullLines: ['abc\n', 'def\n', 'jkl\n', ''],
          baseLine: 0,
          editLine: 0,
          editCh: 3,
          oldval: [''],
          newval: ['', '']
        });
        let expectedCell = shallowCopy(codeCellStub);
        expectedCell.source = 'abc\ndef\njkl\n';
        expect(model.remote).to.be(expectedCell.source);
        let diff = stripSource(nbmodel.cells[0].decisions[0].customDiff)!;
        diff = (diff[0] as IDiffPatchArray).diff!;
        diff = (diff[0] as IDiffPatchArray).diff!;
        expect(diff).to.eql([
          opAddRange(0, ['abc\n', 'def\n']),
          opRemoveRange(0, 1)
        ]);
        expect(nbmodel.cells[0].deleteCell).to.be(false);
        expect(nbmodel.cells[0].decisions.length).to.be(1);
        expect(nbmodel.cells[0].decisions[0].absolutePath).to.eql(['cells']);
      });

      it('should handle a sequence of character and line insertions', () => {
        let nbcontent = shallowCopy(notebookStub);
        let cell = shallowCopy(codeCellStub);
        cell.source = 'abcdef\nghi\njkl\nmnop\n';
        nbcontent.cells = [cell];
        let decisions: IMergeDecision[] = [{
          'common_path': ['cells'],
          'local_diff': [opRemoveRange(0, 1)],
          'action': 'local'
        }];
        let nbmodel = new NotebookMergeModel(nbcontent, decisions);
        let model = nbmodel.cells[0].merged.source;
        // Insert new line
        updateModel({
          model: model,
          fullLines: ['abcdef\n', 'ghi\n', '\n', 'jkl\n', 'mnop\n', ''],
          baseLine: 2,
          editLine: 2,
          editCh: 0,
          oldval: [''],
          newval: ['', '']
        });
        updateModel({
          model: model,
          fullLines: ['abcdef\n', 'ghi\n', '1\n', 'jkl\n', 'mnop\n', ''],
          baseLine: 2,
          editLine: 2,
          editCh: 0,
          oldval: [''],
          newval: ['1']
        });
        updateModel({
          model: model,
          fullLines: ['abcdef\n', 'ghi\n', '13\n', 'jkl\n', 'mnop\n', ''],
          baseLine: 2,
          editLine: 2,
          editCh: 1,
          oldval: [''],
          newval: ['3']
        });
        updateModel({
          model: model,
          fullLines: ['abcdef\n', 'ghi\n', '123\n', 'jkl\n', 'mnop\n', ''],
          baseLine: 2,
          editLine: 2,
          editCh: 1,
          oldval: [''],
          newval: ['2']
        });
        // Insert new line
        updateModel({
          model: model,
          fullLines: ['abcdef\n', '\n', 'ghi\n', '123\n', 'jkl\n', 'mnop\n', ''],
          baseLine: 1,
          editLine: 1,
          editCh: 0,
          oldval: [''],
          newval: ['', '']
        });
        updateModel({
          model: model,
          fullLines: ['abcdef\n', '4\n', 'ghi\n', '123\n', 'jkl\n', 'mnop\n', ''],
          baseLine: 1,
          editLine: 1,
          editCh: 0,
          oldval: [''],
          newval: ['4']
        });
        updateModel({
          model: model,
          fullLines: ['abcdef\n', '45\n', 'ghi\n', '123\n', 'jkl\n', 'mnop\n', ''],
          baseLine: 1,
          editLine: 1,
          editCh: 1,
          oldval: [''],
          newval: ['5']
        });
        updateModel({
          model: model,
          fullLines: ['abcdef\n', '45\n', '6ghi\n', '123\n', 'jkl\n', 'mnop\n', ''],
          baseLine: 1,
          editLine: 2,
          editCh: 0,
          oldval: [''],
          newval: ['6']
        });
        updateModel({
          model: model,
          fullLines: ['abcdef\n', '45\n', '67ghi\n', '123\n', 'jkl\n', 'mnop\n', ''],
          baseLine: 1,
          editLine: 2,
          editCh: 1,
          oldval: [''],
          newval: ['7']
        });
        let expectedCell = shallowCopy(codeCellStub);
        expectedCell.source = 'abcdef\n45\n67ghi\n123\njkl\nmnop\n';
        expect(model.remote).to.be(expectedCell.source);
        let diff = stripSource(nbmodel.cells[0].decisions[0].customDiff)!;
        diff = (diff[0] as IDiffPatchArray).diff!;
        diff = (diff[0] as IDiffPatchArray).diff!;
        expect(diff).to.eql([
          opAddRange(1, ['45\n', '67ghi\n']),
          opRemoveRange(1, 1),
          opAddRange(2, ['123\n'])
        ]);
        expect(nbmodel.cells[0].deleteCell).to.be(false);
        expect(nbmodel.cells[0].decisions.length).to.be(1);
        expect(nbmodel.cells[0].decisions[0].absolutePath).to.eql(['cells']);
      });

    });

  });

});
