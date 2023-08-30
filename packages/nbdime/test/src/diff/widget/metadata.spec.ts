// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
globalThis.DragEvent = class DragEvent {} as any;

import {
    createDirectStringDiffModel
} from '../../../../src/diff/model/string';

import {
  MetadataDiffWidget
} from '../../../../src/diff/widget';


describe('diff', () => {

  describe('widget', () => {

    describe('MetadataDiffWidget', () => {

      it('should create a widget for an unchanged model', () => {
          let model = createDirectStringDiffModel('{}', '{}');
          let widget = new MetadataDiffWidget(model);
          expect(widget).not.toBe(null);
      });

    });

  });

});
