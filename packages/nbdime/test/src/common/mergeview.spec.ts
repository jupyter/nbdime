// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.

import { MergeView } from '../../../src/common/mergeview';
import {
  createDirectStringDiffModel,
  createPatchStringDiffModel,
  StringDiffModel,
} from '../../../src/diff/model/string';
import { DiffRangeRaw } from '../../../src/diff/range';
import {
  opAddRange,
  opRemoveRange,
  opPatch,
} from '../../../src/diff/diffentries';

describe('common', () => {
  describe('MergeView', () => {
    it('should render an EOF insertion after an earlier changed line', () => {
      let base =
        '# Offending Cell:\n' +
        '    - np.array([1, 0])[:, None, None]\nShared Line';
      let model = createPatchStringDiffModel(base, [
        opPatch(1, [
          opAddRange(26, '*('),
          opAddRange(31, ')*xs.'),
          opRemoveRange(31, 3),
          opAddRange(35, 'dim'),
          opRemoveRange(35, 1),
        ]),
        opPatch(2, [opAddRange(11, '\n')]),
        opAddRange(3, ['\n', 'another line']),
      ]);
      let view = new MergeView({ remote: model });
      try {
        expect(view.base.cm.state.doc.toString()).toBe(base);
        expect(view.right!.remoteEditorWidget.cm.state.doc.toString()).toBe(
          '# Offending Cell:\n' +
            '    - np.array([1, 0])[:, *(None,)*xs.ndim]\n' +
            'Shared Line\n\nanother line',
        );
      } finally {
        view.dispose();
      }
    });

    it.each(['unchanged', 'first\nlast', 'last\n', ''])(
      'should display a final insertion after %p',
      base => {
        let suffix = '\nadded line';
        let remote = base + suffix;
        let model = new StringDiffModel(
          base,
          remote,
          [new DiffRangeRaw(base.length, suffix.length)],
          [],
        );
        let view = new MergeView({ remote: model });
        try {
          expect(view.base.cm.state.doc.toString()).toBe(base);
          expect(view.right!.remoteEditorWidget.cm.state.doc.toString()).toBe(
            remote,
          );
        } finally {
          view.dispose();
        }
      },
    );

    it.each(['unchanged', 'first\nlast', 'last\n', ''])(
      'should display a final deletion after %p',
      remote => {
        let suffix = '\nremoved line';
        let base = remote + suffix;
        let model = new StringDiffModel(
          base,
          remote,
          [],
          [new DiffRangeRaw(remote.length, suffix.length)],
        );
        let view = new MergeView({ remote: model });
        try {
          expect(view.base.cm.state.doc.toString()).toBe(base);
          expect(view.right!.remoteEditorWidget.cm.state.doc.toString()).toBe(
            remote,
          );
        } finally {
          view.dispose();
        }
      },
    );

    it('should be initialized for unchanged diff', () => {
      let orig = 'Value';
      let remote = createDirectStringDiffModel(orig, orig);
      let p = new MergeView({
        remote,
      });
      expect(p).not.toBe(null);
    });
  });
});
