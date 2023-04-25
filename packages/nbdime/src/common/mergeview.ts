// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.

// This code is based on the CodeMirror mergeview.js source:
// CodeMirror, copyright (c) by Marijn Haverbeke and others
// Distributed under an MIT license: http://codemirror.net/LICENSE

'use strict';

/*import * as CodeMirror from 'codemirror';*/

/*import { Widget, Panel } from '@lumino/widgets';*/

import { Panel } from '@lumino/widgets';

import type { IStringDiffModel } from '../diff/model';

/*import { DecisionStringDiffModel } from '../merge/model';

import type { DiffRangePos } from '../diff/range';

import { ChunkSource, Chunk, lineToNormalChunks } from '../chunking';

import { EditorWidget } from './editor';
*/

/* import {
  valueIn, hasEntries, splitLines, copyObj
} from './util'; */


import type { EditorView } from '@codemirror/view';



/**
 * A wrapper view for showing StringDiffModels in a MergeView
 */
export function createNbdimeMergeView(remote: IStringDiffModel): MergeView;
export function createNbdimeMergeView(
  remote: IStringDiffModel | null,
  local: IStringDiffModel | null,
  merged: IStringDiffModel,
  readOnly?: boolean
): MergeView;
export function createNbdimeMergeView(
  remote: IStringDiffModel | null,
  local?: IStringDiffModel | null,
  merged?: IStringDiffModel,
  readOnly?: boolean
): MergeView {
  let opts: IMergeViewEditorConfiguration = {
    remote,
    local,
    merged,
    readOnly,
    orig: null
  };
  /*opts.collapseIdentical = true;*/
  let mergeview = new MergeView(opts);
  /*let editors: DiffView[] = [];*/
 /*  let editors: EditorView[] = [];
  if (mergeview.left) {
    editors.push(mergeview.left);
  }
  if (mergeview.right) {
    editors.push(mergeview.right);
  }
  if (mergeview.merge) {
    editors.push(mergeview.merge);
  } */

/*   let mimetype = (remote || merged!).mimetype;
  if (mimetype) {
    // Set the editor mode to the MIME type.
    for (let e of editors) {
      e.ownWidget.model.mimeType = mimetype;
    }
    mergeview.base.model.mimeType = mimetype;
  } */
  return mergeview;
}
export interface IMergeViewEditorConfiguration
  extends CodeMirror.EditorConfiguration {
  /**
   * When true stretches of unchanged text will be collapsed. When a number is given, this indicates the amount
   * of lines to leave visible around such stretches (which defaults to 2). Defaults to false.
   */
  collapseIdentical?: boolean | number;

  /**
   * Original value, not used
   */
  orig: any;

  /**
   * Provides remote diff of document to be shown on the right of the base.
   * To create a diff view, provide only remote.
   */
  remote: IStringDiffModel | null;

  /**
   * Provides local diff of the document to be shown on the left of the base.
   * To create a diff view, omit local.
   */
  local?: IStringDiffModel | null;

  /**
   * Provides the partial merge input for a three-way merge.
   */
  merged?: IStringDiffModel;

  /**
   * When true, the base of a three-way merge is shown. Defaults to true.
   */
  showBase?: boolean;

  /**
   * When true, changed pieces of text are highlighted. Defaults to true.
   */
  showDifferences?: boolean;
}

// Merge view, containing 1 or 2 diff views.
export class MergeView extends Panel {
  constructor(options: IMergeViewEditorConfiguration) {
    super();
    this.options = options;
    this.editorA = null;
    this.editorB = null;
    const labelElement = document.createElement('label');
    this.node.appendChild(labelElement);

  }


  options: any;
  editorA: EditorView | null;
  editorB: EditorView | null
  protected _input: HTMLInputElement;
}

