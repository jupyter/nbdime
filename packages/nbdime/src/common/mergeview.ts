// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.

// This code is based on the CodeMirror mergeview.js source:
// CodeMirror, copyright (c) by Marijn Haverbeke and others
// Distributed under an MIT license: http://codemirror.net/LICENSE

'use strict';

import {
  Extension,
  StateEffect,
  StateField,
  ChangeDesc,
  RangeSetBuilder,
  RangeSet,
} from '@codemirror/state';

import {
  EditorView,
  Decoration,
  DecorationSet,
  WidgetType,
  GutterMarker,
  gutter,
  BlockInfo,
} from '@codemirror/view';

import type { CodeEditor } from '@jupyterlab/codeeditor';

import { Widget, Panel } from '@lumino/widgets';

import type { IStringDiffModel } from '../diff/model';

import { DecisionStringDiffModel } from '../merge/model';

import { offsetToPos, posToOffset, type DiffRangePos } from '../diff/range';

import { ChunkSource, Chunk, lineToNormalChunks } from '../chunking';

import {
  EditorWidget,
  IEditorWidgetOptions,
  createEditorFactory,
} from './editor';

import { valueIn, hasEntries, splitLines } from './util';

const PICKER_SYMBOL = '\u27ad';
const CONFLICT_MARKER = '\u26A0';

export enum DIFF_OP {
  DIFF_DELETE = -1,
  DIFF_INSERT = 1,
  DIFF_EQUAL = 0,
}

export enum EventDirection {
  INCOMING,
  OUTGOING,
}

const GUTTER_PICKER_CLASS = 'jp-Merge-gutter-picker';
const GUTTER_CONFLICT_CLASS = 'jp-Merge-gutter-conflict';
const CHUNK_CONFLICT_CLASS = 'jp-Merge-conflict';

export type EditorDecorationsDict = {
  [key: string]: Decoration;
  chunk: Decoration;
  start: Decoration;
  end: Decoration;
  conflict: Decoration;
  endEmpty: Decoration;
  inserted: Decoration;
  deleted: Decoration;
};

export type MergeViewDecorationDict = {
  [key: string]: EditorDecorationsDict;
  left: EditorDecorationsDict;
  right: EditorDecorationsDict;
  localMerge: EditorDecorationsDict;
  remoteMerge: EditorDecorationsDict;
  customMerge: EditorDecorationsDict;
  eitherMerge: EditorDecorationsDict;
  mixedMerge: EditorDecorationsDict;
};

const conflictDecoration = Decoration.line({ class: CHUNK_CONFLICT_CLASS });
const lineHighlightTypeList = ['chunk', 'conflict', 'start', 'end'];

namespace Private {
  export function buildEditorDecorationDict(
    editorType: string,
    chunkAction?: string,
  ) {
    const suffix: string = chunkAction ? '-' + chunkAction : '';
    const prefix: string = 'cm-merge' + '-' + editorType;
    const dict: EditorDecorationsDict = {
      chunk: Decoration.line({ class: prefix + '-chunk' + suffix }),
      start: Decoration.line({
        class: prefix + '-chunk' + '-' + 'start' + suffix,
      }),
      end: Decoration.line({ class: prefix + '-chunk' + '-' + 'end' + suffix }),
      endEmpty: Decoration.line({
        class: prefix + '-chunk' + '-' + 'end' + suffix + '-empty',
      }),
      conflict: conflictDecoration,
      inserted: Decoration.mark({ class: prefix + '-' + 'inserted' }),
      deleted: Decoration.mark({ class: prefix + '-' + 'deleted' }),
    };
    return dict;
  }
}

const mergeViewDecorationDict: MergeViewDecorationDict = {
  left: Private.buildEditorDecorationDict('l'),
  right: Private.buildEditorDecorationDict('r'),
  localMerge: Private.buildEditorDecorationDict('m', 'local'),
  remoteMerge: Private.buildEditorDecorationDict('m', 'remote'),
  customMerge: Private.buildEditorDecorationDict('m', 'custom'),
  eitherMerge: Private.buildEditorDecorationDict('m', 'either'),
  mixedMerge: Private.buildEditorDecorationDict('m', 'mixed'),
};

function getCommonEditorExtensions(): Extension {
  return [
    gutterMarkerField,
    highlightField,
    paddingWidgetField,
    pickerLineChunkMappingField,
    conflictMarkerLineChunkMappingField,
  ];
}

function applyMapping({ from, to }: any, mapping: ChangeDesc) {
  const map: any = { from: mapping.mapPos(from), to: mapping.mapPos(to) };
  return map;
}

/**
 * Effect for adding highlighting on lines or on characters
 */
const addHighlightEffect = StateEffect.define<{
  from: number;
  to: number;
  highlightType: string;
  decorationKey: string;
}>({
  map: applyMapping,
});

/**
 * Effect for removing highlighting on lines or on characters
 */
const removeHighlightEffect = StateEffect.define<{
  highlightType: string;
  decorationKey: string;
}>({
  map: applyMapping,
});

/**
 * StateField storing information about highlighting elements of an editor
 */
const highlightField = StateField.define<DecorationSet>({
  create() {
    return Decoration.none;
  },
  update(highlightRanges, transaction) {
    highlightRanges = highlightRanges.map(transaction.changes);
    for (let e of transaction.effects) {
      let decoration: Decoration;
      if (e.is(addHighlightEffect)) {
        decoration =
          mergeViewDecorationDict[e.value.decorationKey][e.value.highlightType];
        highlightRanges = highlightRanges.update({
          add: [decoration.range(e.value.from, e.value.to)],
        });
      }
      if (e.is(removeHighlightEffect)) {
        decoration =
          mergeViewDecorationDict[e.value.decorationKey][e.value.highlightType];
        highlightRanges = highlightRanges.update({
          filter: (from: number, to: number, value: Decoration) => {
            return decoration.spec.class !== value.spec.class;
          },
        });
      }
    }
    return highlightRanges;
  },
  provide: field => EditorView.decorations.from(field),
});

/**
 * StateField storing information about padding widgets used to keep the alignment between different editors
 */
export const replacePaddingWidgetEffect = StateEffect.define<DecorationSet>({
  map: (value, mapping) => value.map(mapping),
});

/**
 * StateField storing information about padding widgets used to keep the alignment between different editors
 */
export const paddingWidgetField = StateField.define<DecorationSet>({
  create: () => Decoration.none,
  update: (paddingWidgetRanges, transaction) => {
    for (let e of transaction.effects) {
      if (e.is(replacePaddingWidgetEffect)) {
        return e.value;
      }
    }
    return paddingWidgetRanges.map(transaction.changes);
  },
  provide: field => EditorView.decorations.from(field),
});

/**
 * Widget used for aligning lines of different editors that need to be at the same distance from the top of the document
 */
class PaddingWidget extends WidgetType {
  constructor(size: number) {
    super();
    this.size = size;
  }
  toDOM() {
    let elt = document.createElement('div');
    elt.className = 'cm-merge-spacer';
    elt.style.height = this.size + 'px';
    elt.style.minWidth = '1px';

    return elt;
  }
  size: number;
}

/**
 * Effect for adding a gutter marker
 */
const addGutterMarkerEffect = StateEffect.define<{
  from: number;
  block: boolean;
  on: boolean;
  type: string;
}>({
  map: (val, mapping) => ({
    from: mapping.mapPos(val.from),
    block: val.block,
    on: val.on,
    type: val.type,
  }),
});

/**
 * Effect for removing a gutter marker
 */
const removeGutterMarkerEffect = StateEffect.define<{ type: string }>({
  map: val => ({ type: val.type }),
});

class MergeMarker extends GutterMarker {
  constructor(options: { symbol: string; className: string; block: boolean }) {
    super();
    this._symbol = options.symbol;
    this._className = options.className;
    this._block = options.block;
  }
  get isBlock() {
    return this._block;
  }
  toDOM() {
    let pickerMarker = elt('div', this._symbol);
    pickerMarker.className = this._className;
    return pickerMarker;
  }
  private _symbol: string;
  private _className: string;
  private _block: boolean;
}

/**
 * StateField storing information about gutter markers (picker and conflict ones)
 */
const gutterMarkerField = StateField.define<RangeSet<MergeMarker>>({
  create: () => {
    return RangeSet.empty;
  },
  update: (gutters, transaction) => {
    gutters = gutters.map(transaction.changes);
    for (let e of transaction.effects) {
      if (e.is(addGutterMarkerEffect)) {
        if (e.value.on) {
          const marker: MergeMarker =
            e.value.type === 'picker'
              ? e.value.block
                ? pickerBlockMarker
                : pickerMarker
              : e.value.block
              ? conflictBlockMarker
              : conflictMarker;
          gutters = gutters.update({ add: [marker.range(e.value.from)] });
        }
      }
      if (e.is(removeGutterMarkerEffect)) {
        gutters = RangeSet.empty;
      }
    }
    return gutters;
  },
});

/**
 * Picker gutter marker DOM Element ➭
 */
const pickerMarker = new MergeMarker({
  symbol: PICKER_SYMBOL,
  className: GUTTER_PICKER_CLASS,
  block: false,
});
const pickerBlockMarker = new MergeMarker({
  symbol: PICKER_SYMBOL,
  className: GUTTER_PICKER_CLASS,
  block: true,
});

/**
 * Conflict gutter marker DOM Element ⚠
 */
const conflictMarker = new MergeMarker({
  symbol: CONFLICT_MARKER,
  className: GUTTER_CONFLICT_CLASS,
  block: false,
});
const conflictBlockMarker = new MergeMarker({
  symbol: CONFLICT_MARKER,
  className: GUTTER_CONFLICT_CLASS,
  block: true,
});

/**
 * Effect for adding a mapping between a line and a chunk
 * This is used for adding the gutters at the right place : there is a single gutter marker associated with each chunk
 */
const addLineChunkMappingEffect = StateEffect.define<{
  line: number;
  chunk: Chunk;
  type: String;
}>({
  map: (val, mapping) => ({
    line: mapping.mapPos(val.line),
    chunk: val.chunk,
    type: val.type,
  }),
});

/**
 * Effect for removing a mapping between a line and a chunk
 * This is used for removing the gutters from the right place there is a single gutter marker associated with each chunk
 */
const removeLineChunkMappingEffect = StateEffect.define<{ type: String }>({
  map: val => ({ type: val.type }),
});

/**
 * StateField storing information about the mapping between a line and a chunk for picker gutter markers
 */
const pickerLineChunkMappingField = StateField.define<Map<number, Chunk>>({
  create: () => {
    return new Map();
  },
  update: (lineChunkMapping, transaction) => {
    let newLineChunkMapping = lineChunkMapping;
    for (let e of transaction.effects) {
      if (e.is(addLineChunkMappingEffect) && e.value.type === 'picker') {
        newLineChunkMapping.set(e.value.line, e.value.chunk);
      }
    }
    return newLineChunkMapping;
  },
});

/**
 * StateField storing information about the mapping between a line and a chunk for conflict gutter markers
 */
const conflictMarkerLineChunkMappingField = StateField.define<
  Map<number, Chunk>
>({
  create: () => {
    return new Map();
  },
  update: (lineChunkMapping, transaction) => {
    let newLineChunkMapping = lineChunkMapping;
    for (let e of transaction.effects) {
      if (e.is(addLineChunkMappingEffect) && e.value.type === 'conflict') {
        newLineChunkMapping.set(e.value.line, e.value.chunk);
      }
    }
    return newLineChunkMapping;
  },
});

export interface IMergeViewOptions {
  remote: IStringDiffModel | null;
  local?: IStringDiffModel | null;
  merged?: IStringDiffModel;
  readOnly?: boolean | string;
  factory?: CodeEditor.Factory;
}

/**
 * A wrapper view for showing StringDiffModels in a MergeView
 */
export function createNbdimeMergeView(options: IMergeViewOptions): MergeView {
  const { remote, local, merged, readOnly, factory } = options;
  let opts: IMergeViewEditorConfiguration = {
    remote,
    local,
    merged,
    config: { readOnly },
    factory: factory ?? createEditorFactory(),
  };

  let mergeview = new MergeView(opts);
  let editors: DiffView[] = [];
  if (mergeview.left) {
    editors.push(mergeview.left);
  }
  if (mergeview.right) {
    editors.push(mergeview.right);
  }
  if (mergeview.merge) {
    editors.push(mergeview.merge);
  }

  let mimetype = (remote || merged!).mimetype;
  if (mimetype) {
    // Set the editor mode to the MIME type.
    for (let e of editors) {
      e.remoteEditorWidget.model.mimeType = mimetype;
    }
    mergeview.base.model.mimeType = mimetype;
  }
  return mergeview;
}

/**
 * Used by MergeView to show diff in a string diff model
 */
export class DiffView {
  constructor(
    model: IStringDiffModel,
    type: 'left' | 'right' | 'merge',
    options: IMergeViewEditorConfiguration,
  ) {
    this._model = model;
    this._type = type;
    let remoteValue = this._model.remote || '';
    this._remoteEditorWidget = new EditorWidget({
      ...options,
      value: remoteValue,
    });
  }

  init(baseWidget: EditorWidget) {
    this._baseEditorWidget = baseWidget;
    let baseEditor = this._baseEditorWidget.cm;
    let remoteEditor = this._remoteEditorWidget.cm;
    this._lineChunks = this._model.getLineChunks();
    this._chunks = lineToNormalChunks(this._lineChunks);
    this.updateView(baseEditor, remoteEditor);
    this.syncScroll(baseEditor, remoteEditor);
  }
  /**
   Update the highlighting in the views of baseEditor and remoteEditor
   */
  updateView(baseEditor: EditorView, remoteEditor: EditorView) {
    this.clearHighlighting(
      remoteEditor,
      this._model.additions,
      this._chunks,
      DIFF_OP.DIFF_INSERT,
    );

    this.clearHighlighting(
      baseEditor,
      this._model.deletions,
      this._chunks,
      DIFF_OP.DIFF_DELETE,
    );

    this.updateHighlighting(
      remoteEditor,
      this._model.additions,
      this._chunks,
      DIFF_OP.DIFF_INSERT,
    );

    this.updateHighlighting(
      baseEditor,
      this._model.deletions,
      this._chunks,
      DIFF_OP.DIFF_DELETE,
    );
  }
  /**
  Update the chunks once a version has been picked
   */
  syncModel() {
    if (!this.modelInvalid()) {
      return;
    }
    let editor = this.remoteEditorWidget.cm;
    let updatedLineChunks = this._model.getLineChunks();
    let updatedChunks = lineToNormalChunks(updatedLineChunks);
    if (this._model.remote === editor.state.doc.toString()) {
      // Nothing to do except update chunks
      this._lineChunks = updatedLineChunks;
      this._chunks = updatedChunks;
      return;
    }
    let cursor = editor.state.selection.main.head;
    let newLines = splitLines(this._model.remote!);
    editor.dispatch(
      {
        changes: {
          from: 0,
          to: editor.state.doc.length,
          insert: newLines.slice(0, newLines.length).join(''),
        },
      },
      { selection: { anchor: cursor } },
    );
    this._lineChunks = updatedLineChunks;
    this._chunks = updatedChunks;
  }
  /**
Add a gap DOM element between 2 editors
 */
  buildGap(): HTMLElement {
    let lock = (this._lockButton = elt(
      'div',
      undefined,
      'cm-merge-scrolllock',
    ));
    lock.title = 'Toggle locked scrolling';
    let lockWrap = elt('div', [lock], 'cm-merge-scrolllock-wrap');
    lock.innerHTML = '\u21db&nbsp;&nbsp;\u21da';
    lock.addEventListener('scroll', event => {
      this.setScrollLock(!this._lockScroll);
    });
    let gap = elt('div', [lockWrap], 'cm-merge-gap');
    this._gap = gap;
    return this._gap;
  }

  setScrollLock(val: boolean, action?: boolean) {
    this._lockScroll = val;
    if (this._lockButton) {
      this._lockButton.innerHTML = val
        ? '\u21db\u21da'
        : '\u21db&nbsp;&nbsp;\u21da';
    }
  }

  private modelInvalid(): boolean {
    return (
      this._model instanceof DecisionStringDiffModel && this._model.invalid
    );
  }

  /**
   * Synchronize the scrolling between editors.
   * srcEditor refers to the source editor from which the scrolling is done and listened
   * destEditor is the destination editor whose scrolling is synchronized with the one of srcEditor.
   */
  private syncScroll(srcEditor: EditorView, destEditor: EditorView): void {
    if (this.modelInvalid()) {
      return;
    }
    let srcScroller = srcEditor.scrollDOM;
    let destScroller = destEditor.scrollDOM;
    srcScroller.addEventListener('scroll', event => {
      window.requestAnimationFrame(function () {
        destScroller.scrollLeft = srcScroller.scrollLeft;
      });
    });

    destScroller.addEventListener('scroll', event => {
      window.requestAnimationFrame(function () {
        srcScroller.scrollLeft = destScroller.scrollLeft;
      });
    });
  }

  /**
   * The decorationKey is used to have access to the correct css class associated to a given decoration type
   */
  private getDecorationKey(sources: ChunkSource[]): string {
    let s: string = this._type;
    let res: string = s;
    if (this._type === 'merge') {
      s = sources[0].action;
      res = s + 'Merge';
      if (sources.length > 1) {
        for (let si of sources.slice(1)) {
          if (si.action !== s) {
            res = 'mixedMerge';
            break;
          }
        }
      }
    }
    return res;
  }

  private getConflictState(sources: ChunkSource[]): boolean {
    let conflict = false;
    if (sources.length > 0) {
      for (let s of sources) {
        if (s.decision.conflict) {
          conflict = true;
          break;
        }
      }
    }
    return conflict;
  }

  /**
   * Create effects related to gutter markers
   */
  private createGutterEffects(
    editor: EditorView,
    chunk: Chunk,
    from: number,
    type: 'picker' | 'conflict',
    block: boolean = false,
  ) {
    let effects: StateEffect<unknown>[] = [];

    let gutterEffect = addGutterMarkerEffect.of({
      from: from,
      on: true,
      type: type,
      block: block,
    });
    effects.push(gutterEffect);

    effects.push(
      addLineChunkMappingEffect.of({
        line: offsetToPos(editor.state.doc, from).line,
        chunk: chunk,
        type: type,
      }),
    );
    return effects;
  }

  /**
   * Build line background effects and gutter markers effects
   */
  private buildLineEffects(editor: EditorView, chunkArray: Chunk[]) {
    let effects: StateEffect<unknown>[] = [];
    let isbaseEditor = editor === this._baseEditorWidget.cm;
    for (let chunk of chunkArray) {
      let decorationKey = this.getDecorationKey(chunk.sources);
      let conflict = this.getConflictState(chunk.sources);
      let chunkFirstLine: number;
      let chunkLastLine: number;

      if (isbaseEditor) {
        chunkFirstLine = chunk.baseFrom;
        chunkLastLine = chunk.baseTo;
      } else {
        chunkFirstLine = chunk.remoteFrom;
        chunkLastLine = chunk.remoteTo;
      }
      for (let i = chunkFirstLine; i < chunkLastLine; i++) {
        let pos: any = { line: i, column: 0 };
        let startingOffset = posToOffset(editor.state.doc, pos);

        effects.push(
          addHighlightEffect.of({
            from: startingOffset,
            to: startingOffset,
            highlightType: 'chunk',
            decorationKey: decorationKey,
          }),
        );

        if (conflict) {
          effects.push(
            addHighlightEffect.of({
              from: startingOffset,
              to: startingOffset,
              highlightType: 'conflict',
              decorationKey: decorationKey,
            }),
          );
        }
        if (i === chunkFirstLine) {
          effects.push(
            addHighlightEffect.of({
              from: startingOffset,
              to: startingOffset,
              highlightType: 'start',
              decorationKey: decorationKey,
            }),
          );

          if (!decorationKey.includes('Merge')) {
            // For all editors except merge editor, add a picker button
            effects = effects.concat(
              this.createGutterEffects(editor, chunk, startingOffset, 'picker'),
            );
          } else if (editor === this._baseEditorWidget.cm) {
            for (let s of chunk.sources) {
              if (
                s.decision.action === 'custom' &&
                !hasEntries(s.decision.localDiff) &&
                !hasEntries(s.decision.remoteDiff)
              ) {
                // We have a custom decision, add picker on base only!
                effects = effects.concat(
                  this.createGutterEffects(
                    editor,
                    chunk,
                    startingOffset,
                    'picker',
                  ),
                );
              }
            }
          } else if (conflict && editor === this.remoteEditorWidget.cm) {
            effects = effects.concat(
              this.createGutterEffects(
                editor,
                chunk,
                startingOffset,
                'conflict',
              ),
            );
          }
        }
        if (i === chunkLastLine - 1) {
          effects.push(
            addHighlightEffect.of({
              from: startingOffset,
              to: startingOffset,
              highlightType: 'end',
              decorationKey: decorationKey,
            }),
          );
        }
      }
      if (chunkFirstLine === chunkLastLine) {
        // When the chunk is empty, make sure a horizontal line shows up
        const startingOffset = posToOffset(editor.state.doc, {
          line: chunkFirstLine,
          column: 0,
        });
        effects.push(
          addHighlightEffect.of({
            from: startingOffset,
            to: startingOffset,
            highlightType: 'endEmpty',
            decorationKey: decorationKey,
          }),
        );
        if (!decorationKey.includes('Merge')) {
          effects = effects.concat(
            this.createGutterEffects(
              editor,
              chunk,
              startingOffset,
              'picker',
              true,
            ),
          );
        } else if (conflict) {
          // Add conflict markers on editor, if conflicted
          effects = effects.concat(
            this.createGutterEffects(
              editor,
              chunk,
              startingOffset,
              'conflict',
              true,
            ),
          );
        }
      }
    }
    return effects;
  }

  /**
   * Remove line background effects and gutter markers effects
   */
  private clearLineEffects(editor: EditorView, chunkArray: Chunk[]) {
    let effects: StateEffect<unknown>[] = [];

    for (let chunk of chunkArray) {
      let sources: ChunkSource[] = chunk.sources;
      let decorationKey = this.getDecorationKey(sources);
      for (let highlightType of lineHighlightTypeList) {
        effects.push(
          removeHighlightEffect.of({
            highlightType: highlightType,
            decorationKey: decorationKey,
          }),
        );
      }
    }
    if (editor !== this._baseEditorWidget.cm) {
      effects.push(removeGutterMarkerEffect.of({ type: 'all' }));
      effects.push(removeLineChunkMappingEffect.of({ type: 'picker' }));
      effects.push(removeLineChunkMappingEffect.of({ type: 'conflict' }));
    }
    return effects;
  }

  /**
   * Build character highlighting effects
   */
  private buildCharacterHighlighting(
    editor: EditorView,
    diffRanges: DiffRangePos[],
    markType: DIFF_OP,
  ) {
    const effects: StateEffect<unknown>[] = [];
    const sources: ChunkSource[] = [];
    if (markType === DIFF_OP.DIFF_INSERT || markType === DIFF_OP.DIFF_DELETE) {
      const highlightType: string =
        markType === DIFF_OP.DIFF_DELETE ? 'deleted' : 'inserted';

      for (let r of diffRanges) {
        if (r.source !== undefined) {
          sources.push(r.source);
        }
        const startingOffset = posToOffset(editor.state.doc, {
          line: r.from.line,
          column: r.from.column,
        });
        const endingOffset = posToOffset(editor.state.doc, {
          line: r.to.line,
          column: r.to.column,
        });
        effects.push(
          addHighlightEffect.of({
            from: startingOffset,
            to: endingOffset,
            highlightType: highlightType,
            decorationKey: this.getDecorationKey(sources),
          }),
        );
      }
    }
    return effects;
  }

  /**
  Clear character highlighting effects
  */
  private clearCharacterHighlighting(
    editor: EditorView,
    diffRanges: DiffRangePos[],
    markType: DIFF_OP,
  ) {
    let effects: StateEffect<unknown>[] = [];
    let sources: ChunkSource[] = [];
    if (markType === DIFF_OP.DIFF_INSERT || markType === DIFF_OP.DIFF_DELETE) {
      let highlightType: string =
        markType === DIFF_OP.DIFF_DELETE ? 'deleted' : 'inserted';
      for (let r of diffRanges) {
        if (r.source !== undefined) {
          sources.push(r.source);
        }
        let decorationKey = this.getDecorationKey(sources);
        effects.push(
          removeHighlightEffect.of({
            highlightType: highlightType,
            decorationKey: decorationKey,
          }),
        );
      }
    }
    return effects;
  }

  /**
  Build line effects (highlight and gutters) and character highlighting effects and dispatch them
   */
  private updateHighlighting(
    editor: EditorView,
    diffRanges: DiffRangePos[],
    chunkArray: Chunk[],
    type: DIFF_OP,
  ) {
    const LineHighlightEffects: StateEffect<unknown>[] = this.buildLineEffects(
      editor,
      chunkArray,
    );
    const MarkHighlightEffects: StateEffect<unknown>[] =
      this.buildCharacterHighlighting(editor, diffRanges, type);
    const effects: StateEffect<unknown>[] =
      LineHighlightEffects.concat(MarkHighlightEffects);
    editor.dispatch({ effects });
  }

  /**
  Clear line effects (highlight and gutters) and character highlighting effects and dispatch them
   */
  private clearHighlighting(
    editor: EditorView,
    diffRanges: DiffRangePos[],
    chunkArray: Chunk[],
    type: DIFF_OP,
  ) {
    const clearLineEffects: StateEffect<unknown>[] = this.clearLineEffects(
      editor,
      chunkArray,
    );
    const clearCharacterHighlightEffects: StateEffect<unknown>[] =
      this.clearCharacterHighlighting(editor, diffRanges, type);
    const effects: StateEffect<unknown>[] = clearLineEffects.concat(
      clearCharacterHighlightEffects,
    );
    editor.dispatch({ effects });
  }

  get remoteEditorWidget(): EditorWidget {
    return this._remoteEditorWidget;
  }

  get baseEditorWidget(): EditorWidget {
    return this._baseEditorWidget;
  }

  get lineChunks(): Chunk[] {
    return this._lineChunks;
  }

  get model(): IStringDiffModel {
    return this._model;
  }

  private _baseEditorWidget: EditorWidget;
  private _remoteEditorWidget: EditorWidget;
  private _model: IStringDiffModel;
  private _type: string;
  private _chunks: Chunk[];
  private _lineChunks: Chunk[];
  private _gap: HTMLElement;
  private _lockScroll: boolean;
  private _lockButton: HTMLElement;
}

/**
 * From a line in base, find the matching line in another editor by line chunks
 *
 */
function getMatchingEditLineLC(toMatch: Chunk, chunks: Chunk[]): number {
  let editLine = toMatch.baseFrom;
  for (let i = 0; i < chunks.length; ++i) {
    let chunk = chunks[i];
    if (chunk.baseFrom === editLine) {
      return chunk.remoteTo;
    }
    if (chunk.baseFrom > editLine) {
      break;
    }
  }
  return toMatch.baseTo;
}

/**
 * Find which line numbers align with each other, in the
 * set of DiffViews. The returned array is of the format:
 *
 * [ aligned line #1:[Edit line number, (DiffView#1 line number, DiffView#2 line number,) ...],
 *   aligned line #2 ..., etc.]
 */

function findAlignedLines(dvs: DiffView[]): number[][] {
  let linesToAlign: number[][] = [];
  let ignored: number[] = [];

  // First fill directly from first DiffView
  let dv = dvs[0];
  let others = dvs.slice(1);
  for (let i = 0; i < dv.lineChunks.length; i++) {
    let chunk = dv.lineChunks[i];
    let lines = [chunk.baseTo, chunk.remoteTo];

    for (let o of others) {
      lines.push(getMatchingEditLineLC(chunk, o.lineChunks));
    }
    if (
      linesToAlign.length > 0 &&
      linesToAlign[linesToAlign.length - 1][0] === lines[0]
    ) {
      let last = linesToAlign[linesToAlign.length - 1];
      for (let j = 0; j < lines.length; ++j) {
        last[j] = Math.max(last[j], lines[j]);
      }
    } else {
      if (linesToAlign.length > 0) {
        let prev = linesToAlign[linesToAlign.length - 1];
        let diff: number | null = lines[0] - prev[0];
        for (let j = 1; j < lines.length; ++j) {
          if (diff !== lines[j] - prev[j]) {
            diff = null;
            break;
          }
        }
        if (diff === null) {
          linesToAlign.push(lines);
        } else {
          ignored.push(lines[0]);
          continue;
        }
      } else {
        linesToAlign.push(lines);
      }
    }
  }
  // Then fill any chunks from remaining DiffView, which are not already added
  for (let o = 0; o < others.length; o++) {
    for (let i = 0; i < others[o].lineChunks.length; i++) {
      let chunk = others[o].lineChunks[i];
      // Check against existing matches to see if already consumed:
      let j = 0;
      for (; j < linesToAlign.length; j++) {
        let align = linesToAlign[j];
        if (valueIn(chunk.baseTo, ignored)) {
          // Chunk already consumed, continue to next chunk
          j = -1;
          break;
        } else if (align[0] >= chunk.baseTo) {
          // New chunk, which should be inserted in pos j,
          // such that linesToAlign are sorted on edit line
          break;
        }
      }
      if (j > -1) {
        let lines = [chunk.baseTo, getMatchingEditLineLC(chunk, dv.lineChunks)];
        for (let k = 0; k < others.length; k++) {
          if (k === o) {
            lines.push(chunk.remoteTo);
          } else {
            lines.push(getMatchingEditLineLC(chunk, others[k].lineChunks));
          }
        }
        if (linesToAlign.length > j && linesToAlign[j][0] === chunk.baseTo) {
          let last = linesToAlign[j];
          for (let k = 0; k < lines.length; ++k) {
            last[k] = Math.max(last[k], lines[k]);
          }
        } else {
          linesToAlign.splice(j, 0, lines);
        }
      }
    }
  }
  return linesToAlign;
}
export interface IMergeViewEditorConfiguration
  extends Omit<IEditorWidgetOptions, 'value'> {
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
    this._measuring = -1;
    let remote = options.remote;
    let local = options.local || null;
    let merged = options.merged || null;
    let left: DiffView | null = (this._left = null);
    let right: DiffView | null = (this._right = null);
    let merge: DiffView | null = (this._merge = null);
    let panes: number = 0;
    this._diffViews = [];
    let main = options.remote || options.merged;
    if (!main) {
      throw new Error('Either remote or merged model needs to be specified!');
    }
    const value = main.base !== null ? main.base : main.remote ?? '';

    // Whether merge view should be readonly
    let readOnly = options.config?.readOnly ?? false;

    options.config = {
      ...options.config,
      lineNumbers: options.config?.lineNumbers !== false,
      // For all others:
      readOnly: true,
    };

    if (merged) {
      // Turn off linewrapping for merge view by default, keep for diff
      options.config.lineWrap = options.config.lineWrap ?? false;
    }

    this._aligning = true;

    /**
     * Listener extension to track for changes in the editorView
     */
    const listener = EditorView.updateListener.of(update => {
      if (
        this._measuring < 0 &&
        /*update.heightChanged || */ update.viewportChanged &&
        !update.transactions.some(tr =>
          tr.effects.some(e => e.is(replacePaddingWidgetEffect)),
        )
      ) {
        this.alignViews();
      }
    });

    /**
     * MergeControlGutter to set the gutter in a given editor and the mousedown events for picker markers
     */
    const mergeControlGutter = [
      gutterMarkerField,
      gutter({
        class: 'cm-gutter',
        markers: view => {
          return view.state.field(gutterMarkerField).update({
            filter: (_from, _to, value: MergeMarker) => !value.isBlock,
          });
        },
        widgetMarker: (
          view: EditorView,
          widget: WidgetType,
          block: BlockInfo,
        ): GutterMarker | null => {
          if (!(widget instanceof PaddingWidget)) {
            return null;
          }
          const markers = view.state.field(gutterMarkerField).update({
            filter: (from, _to, value: MergeMarker) =>
              value.isBlock && block.from === from,
          });
          if (markers.size > 1) {
            throw Error('More than one block gutter widget matched');
          }
          if (markers.size === 1) {
            const cursor = markers.iter();
            return cursor.value;
          }
          return null;
        },
        initialSpacer: () => pickerMarker,
        domEventHandlers: {
          mousedown: (editor, line) => {
            this.onGutterClick(editor, line);
            return true;
          },
        },
      }),
    ];

    /*
     * Different cases possible:
     *   - Local and merged supplied: Merge:
     *     - Always use left, right and merge panes
     *     - Use base if `showBase` not set to false
     *   - Only remote supplied: Diff:
     *     - No change: Use ony base editor
     *     - Entire content added/deleted: Use only base editor,
     *       but with different classes
     *     - Partial changes: Use base + right editor
     */
    this._base = new EditorWidget({
      ...options,
      extensions: [
        ...(options.extensions ?? []),
        listener,
        mergeControlGutter,
        getCommonEditorExtensions(),
      ],
      value,
    });

    // START MERGE CASE
    if (merged) {
      this._gridPanel = new Panel();
      this.addWidget(this._gridPanel);
      this._gridPanel.addClass('cm-merge-grid-panel');
      let showBase = options.showBase !== false;

      if (!showBase) {
        this._base.node.style.display = 'hidden';
      }

      let leftWidget: Widget;
      if (!local || local.remote === null) {
        // Local value was deleted
        left = this._left = null;
        leftWidget = new Widget({
          node: elt('div', 'Value missing', 'jp-mod-missing'),
        });
      } else {
        left = this._left = new DiffView(local, 'left', {
          ...options,
          // Copy configuration
          config: { ...options.config },
          extensions: [
            ...(options.extensions ?? []),
            listener,
            mergeControlGutter,
            getCommonEditorExtensions(),
          ],
        });
        this._diffViews.push(left);
        leftWidget = left.remoteEditorWidget;
      }
      this._gridPanel.addWidget(leftWidget);
      leftWidget.addClass('cm-merge-left-editor');

      if (showBase) {
        this._gridPanel.addWidget(this._base);
        this._base.addClass('cm-central-editor');
      }

      let rightWidget: Widget;
      if (!remote || remote.remote === null) {
        // Remote value was deleted
        right = this._right = null;
        rightWidget = new Widget({
          node: elt('div', 'Value missing', 'jp-mod-missing'),
        });
      } else {
        right = this._right = new DiffView(remote, 'right', {
          ...options,
          // Copy configuration
          config: { ...options.config },
          extensions: [
            ...(options.extensions ?? []),
            listener,
            mergeControlGutter,
            getCommonEditorExtensions(),
          ],
        });
        this._diffViews.push(right);
        rightWidget = right.remoteEditorWidget;
      }
      this._gridPanel.addWidget(rightWidget);
      rightWidget.addClass('cm-merge-pane');
      rightWidget.addClass('cm-merge-right-editor');

      merge = this._merge = new DiffView(merged, 'merge', {
        ...options,
        // Copy configuration
        config: { ...options.config, readOnly },
        extensions: [
          ...(options.extensions ?? []),
          listener,
          mergeControlGutter,
          getCommonEditorExtensions(),
        ],
      });
      this._diffViews.push(merge);
      let mergeWidget = merge.remoteEditorWidget;
      this._gridPanel.addWidget(mergeWidget);
      mergeWidget.addClass('cm-merge-editor');
      //END MERGE CASE
      panes = 3 + (showBase ? 1 : 0);
      // START DIFF CASE
    } else if (remote) {
      this._gridPanel = new Panel();
      this.addWidget(this._gridPanel);
      this._gridPanel.addClass('cm-single-panel');
      // If in place for type guard
      this._gridPanel.addWidget(this._base);
      if (remote.unchanged || remote.added || remote.deleted) {
        if (remote.unchanged) {
          this._base.addClass('cm-merge-pane-unchanged');
        } else if (remote.added) {
          this._base.addClass('cm-merge-pane-added');
        } else if (remote.deleted) {
          this._base.addClass('cm-merge-pane-deleted');
        }
        panes = 1;
      } else {
        this._gridPanel = new Panel();
        this.addWidget(this._gridPanel);
        this._gridPanel.addClass('cm-diff-grid-panel');
        // If in place for type guard
        this._gridPanel.addWidget(this._base);
        this._base.addClass('cm-diff-left-editor');
        right = this._right = new DiffView(remote, 'right', {
          ...options,
          // Copy configuration
          config: { ...options.config },
          extensions: [
            ...(options.extensions ?? []),
            listener,
            mergeControlGutter,
            getCommonEditorExtensions(),
          ],
        });
        this._diffViews.push(right);
        let rightWidget = right.remoteEditorWidget;
        rightWidget.addClass('cm-diff-right-editor');
        this.addWidget(new Widget({ node: right.buildGap() }));
        this._gridPanel.addWidget(rightWidget);
        panes = 2;
      }
    }

    this.addClass('cm-merge-' + panes + 'pane');

    for (let dv of [left, right, merge]) {
      if (dv) {
        dv.init(this._base);
      }
    }
    this._aligning = false;
    if (this._diffViews.length > 0) {
      this.scheduleAlignViews();
    }
  }
  /**
   * Align the matching lines of the different editors
   */
  alignViews() {
    let lineHeight = this._base.cm.defaultLineHeight;
    if (this._aligning) {
      return;
    }
    this._aligning = true;
    // Find matching lines
    let linesToAlign = findAlignedLines(this._diffViews);

    // Function modifying DOM to perform alignment:
    let self: MergeView = this;
    let editors: EditorView[] = [self.base.cm];
    let builders: RangeSetBuilder<Decoration>[] = [];
    for (let dv of self._diffViews) {
      editors.push(dv.remoteEditorWidget.cm);
    }
    for (let i = 0; i < editors.length; i++) {
      builders.push(new RangeSetBuilder<Decoration>());
    }

    let sumDeltas = new Array(editors.length).fill(0);
    let nLines = editors.map(editor => editor.state.doc.lines);

    for (let alignment_ of linesToAlign) {
      let alignment = alignment_.slice(0, 3);
      let lastLine = Math.max(...alignment);
      let lineDeltas = alignment.map(
        (line, i) => lastLine - line - sumDeltas[i],
      );
      // If some paddings will be before the current line, it means all other editors
      // must add a padding.
      let minDelta = Math.min(...lineDeltas);
      let correctedDeltas = lineDeltas.map(line => line - minDelta);

      correctedDeltas.forEach((delta, i) => {
        let side = -1;
        let line = alignment[i];

        if (delta > 0 && line < nLines[i]) {
          sumDeltas[i] += delta;

          let offset = posToOffset(editors[i].state.doc, {
            line,
            column: 0,
          });

          builders[i].add(
            offset,
            offset,
            Decoration.widget({
              widget: new PaddingWidget(delta * lineHeight),
              block: true,
              side,
            }),
          );
        }
      });
    }

    // Padding at the last line of the editor
    let totalHeight = nLines.map((line, i) => line + sumDeltas[i]);
    let maxHeight = Math.max(...totalHeight);
    totalHeight.slice(0, 3).forEach((line, i) => {
      if (maxHeight > line) {
        let end = editors[i].state.doc.length;
        let delta = maxHeight - line;
        sumDeltas[i] += delta;
        builders[i].add(
          end,
          end,
          Decoration.widget({
            widget: new PaddingWidget(delta * lineHeight),
            block: true,
            side: 1,
          }),
        );
      }
    });

    for (let i = 0; i < editors.length; i++) {
      let decoSet: DecorationSet = builders[i].finish();
      if (
        !RangeSet.eq([decoSet], [editors[i].state.field(paddingWidgetField)])
      ) {
        editors[i].dispatch({
          effects: replacePaddingWidgetEffect.of(decoSet),
        });
      }
    }
    this._aligning = false;
  }

  /**
   * Used to schedule the call of alignViews
   */
  scheduleAlignViews() {
    if (this._measuring < 0) {
      let win = this._gridPanel.node.ownerDocument.defaultView || window;
      this._measuring = win.requestAnimationFrame(() => {
        this._measuring = -1;
        this.alignViews();
      });
    }
  }

  getMergedValue(): string {
    if (!this.merge) {
      throw new Error('No merged value; missing "merged" view');
    }

    return this.merge.remoteEditorWidget.doc.toString();
  }

  /**
   * Actions and updates performed when a gutter marker is clicked
   */
  private onGutterClick(editor: EditorView, line: BlockInfo): boolean {
    let effects: StateEffect<unknown>[] = [];
    let offset: number = line.from;
    let gutterMarkerline: number = offsetToPos(editor.state.doc, offset).line;
    let isPicker: boolean = editor != this.merge?.remoteEditorWidget.cm;

    if (isPicker) {
      let pickerLineChunksMapping = editor.state.field(
        pickerLineChunkMappingField,
      );
      let chunk: Chunk = pickerLineChunksMapping.get(gutterMarkerline)!;

      if (!(editor == this._base.cm)) {
        for (let source of chunk.sources) {
          source.decision.action = source.action;
        }
      } else if (this.merge && editor === this._base.cm) {
        for (let source of chunk.sources) {
          source.decision.action = 'base';
        }
      }
      for (let i = chunk.sources.length - 1; i >= 0; --i) {
        let source = chunk.sources[i];
        if (this.merge && hasEntries(source.decision.customDiff)) {
          // Custom diffs are cleared on pick,
          // as there is no way to re-pick them
          source.decision.customDiff = [];
        }
      }
      if (chunk.sources.length === 0) {
        // All decisions empty, remove picker
        // In these cases, there should only be one picker, on base
        // so simply remove the one we have here
      }
      effects.push(
        addGutterMarkerEffect.of({
          from: line.from,
          on: false,
          type: 'picker',
          block: false,
        }),
      );
    } else {
      // conflict picker
      let conflictLineChunksMapping = editor.state.field(
        conflictMarkerLineChunkMappingField,
      );
      let chunk: Chunk = conflictLineChunksMapping.get(gutterMarkerline)!;

      for (let source of chunk.sources) {
        if (editor !== this._base.cm) {
          source.decision.conflict = false;
        }
      }
    }
    editor.dispatch({ effects: effects });
    this.updateDiffModels();
    this.updateDiffViews();
    this.alignViews();
    return true;
  }

  /**
   * Update of the models of the diffViews by calling syncModel that updates the chunks
   */
  private updateDiffModels() {
    for (let dv of this._diffViews) {
      if (dv.model instanceof DecisionStringDiffModel) {
        dv.model.invalidate();
      }
      dv.syncModel();
    }
  }

  /**
   * Update of the views of the diffViews by calling updateView
   * Before updating the diffViews, baseEditor needs to be cleared from its pickers
   */
  private updateDiffViews() {
    this.clearBaseEditorPickers();
    for (let dv of this._diffViews) {
      dv.updateView(dv.baseEditorWidget.cm, dv.remoteEditorWidget.cm);
    }
  }
  /**
   * Clear the pickers of the baseEditor
   * The baseEditor is indeed cumulating pickers from different diffViews
   * Since this editor is common to the 3 diffviews
   */
  private clearBaseEditorPickers() {
    let effects: StateEffect<unknown>[] = [];
    effects.push(removeGutterMarkerEffect.of({ type: 'all' }));
    effects.push(removeLineChunkMappingEffect.of({ type: 'picker' }));
    this._base.cm.dispatch({ effects });
  }

  public get left(): DiffView | null {
    return this._left;
  }

  public get right(): DiffView | null {
    return this._right;
  }

  public get merge(): DiffView | null {
    return this._merge;
  }

  public get base(): EditorWidget {
    return this._base;
  }

  private _gridPanel: Panel;
  private _left: DiffView | null;
  private _right: DiffView | null;
  private _merge: DiffView | null;
  private _base: EditorWidget;
  private _diffViews: DiffView[];
  private _aligning: boolean;
  private _measuring: number;
}

/**
 To create DOM element with defined properties
 */
function elt(
  tag: string,
  content?: string | HTMLElement[] | null,
  className?: string | null,
  style?: string | null,
): HTMLElement {
  let e = document.createElement(tag);
  if (className) {
    e.className = className;
  }
  if (style) {
    e.style.cssText = style;
  }
  if (typeof content === 'string') {
    e.appendChild(document.createTextNode(content));
  } else if (content) {
    for (let i = 0; i < content.length; ++i) {
      e.appendChild(content[i]);
    }
  }
  return e;
}
