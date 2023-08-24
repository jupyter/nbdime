// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.

// This code is based on the CodeMirror mergeview.js source:
// CodeMirror, copyright (c) by Marijn Haverbeke and others
// Distributed under an MIT license: http://codemirror.net/LICENSE

'use strict';

import { Widget, Panel } from '@lumino/widgets';

import type { IStringDiffModel } from '../diff/model';

import {
  DecisionStringDiffModel
} from '../merge/model';

import { offsetToPos, posToOffset, type DiffRangePos } from '../diff/range';

import { ChunkSource, Chunk, lineToNormalChunks } from '../chunking';

import { EditorWidget } from './editor';

import { valueIn, hasEntries, splitLines, copyObj } from './util';

import {
  Extension,
  StateEffect,
  StateField,
  ChangeDesc,
  RangeSetBuilder,
  RangeSet
} from '@codemirror/state';

import {
  EditorView,
  Decoration,
  DecorationSet,
  WidgetType,
  GutterMarker,
  gutter,
  BlockInfo
} from '@codemirror/view';

import { LegacyCodeMirror } from '../legacy_codemirror/cmconfig';
const PICKER_SYMBOL = '\u27ad';
const CONFLICT_MARKER = '\u26A0';

export enum DIFF_OP {
  DIFF_DELETE = -1,
  DIFF_INSERT = 1,
  DIFF_EQUAL = 0
}

export enum EventDirection {
  INCOMING,
  OUTGOING
}

export type DiffClasses = {
  [key: string]: string;
  chunk: string;
  start: string;
  end: string;
  insert: string;
  del: string;
  connect: string;
  gutter: string;
};

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

namespace Private {
  export function buildEditorDecorationDict(
    editorType: string,
    chunkAction?: string
  ) {
    const suffix: string = chunkAction ? '-' + chunkAction : '';
    const prefix: string = 'cm-merge' + '-' + editorType;
    const dict: EditorDecorationsDict = {
      chunk: Decoration.line({ class: prefix + '-chunk' + suffix }),
      start: Decoration.line({
        class: prefix + '-chunk' + '-' + 'start' + suffix
      }),
      end: Decoration.line({ class: prefix + '-chunk' + '-' + 'end' + suffix }),
      endEmpty: Decoration.line({
        class: prefix + '-chunk' + '-' + 'end' + suffix + '-empty'
      }),
      conflict: conflictDecoration,
      inserted: Decoration.mark({ class: prefix + '-' + 'inserted'}),
      deleted: Decoration.mark({ class: prefix + '-' + 'deleted'}),
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
  mixedMerge: Private.buildEditorDecorationDict('m', 'mixed')
};

function getCommonEditorExtensions(): Extension {
  return [
    gutterMarkerField,
    highlightField,
    paddingWidgetField,
    pickerLineChunkMappingField,
    conflictMarkerLineChunkMappingField
  ];
}

function applyMapping({ from, to }: any, mapping: ChangeDesc) {
  const map: any = { from: mapping.mapPos(from), to: mapping.mapPos(to) };
  return map;
}
const addHighlightEffect = StateEffect.define<{
  from: number;
  to: number;
  highlightType: string;
  decorationKey: string;
}>({
  map: applyMapping
});

const removeHighlightEffect = StateEffect.define<{
  highlightType: string;
  decorationKey: string;
}>({
  map: applyMapping
});

const highlightField = StateField.define<DecorationSet>({
  create() {
    return Decoration.none;
  },
  update(highlightRanges, transaction) {
    highlightRanges = highlightRanges.map(transaction.changes);
    for (let e of transaction.effects) {
      let decoration: Decoration;
      if (e.is(addHighlightEffect)) {
        decoration = mergeViewDecorationDict[e.value.decorationKey][e.value.highlightType];
        highlightRanges = highlightRanges.update({
          add: [decoration.range(e.value.from, e.value.to)]
        });
      }
      if (e.is(removeHighlightEffect)) {
        decoration = mergeViewDecorationDict[e.value.decorationKey][e.value.highlightType];
        highlightRanges = highlightRanges.update({
          filter: (from: number, to: number, value: Decoration) => {return (decoration.spec.class !== value.spec.class) },
        });
      }
     }
  return highlightRanges;
},
  provide: field => EditorView.decorations.from(field)
});

export const replacePaddingWidgetEffect= StateEffect.define<DecorationSet>({
  map: (value, mapping) => value.map(mapping)
});

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
  provide: field => EditorView.decorations.from(field)
});
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

const addGutterMarkerEffect = StateEffect.define<{pos: number, on: boolean, type: string}>({
  map: (val, mapping) => ({pos: mapping.mapPos(val.pos), on: val.on, type: val.type})
})

const removeGutterMarkerEffect = StateEffect.define<{type: string}>({
  map: (val) => ({type: val.type})
})

const gutterMarkerField = StateField.define<RangeSet<GutterMarker>>({
  create:() => {
    return RangeSet.empty;
  },
  update: (gutters, transaction) => {
    gutters = gutters.map(transaction.changes);
    for (let e of transaction.effects) {
      if (e.is(addGutterMarkerEffect)) {
        if (e.value.on) {
          const marker: GutterMarker = e.value.type === 'picker'? pickerMarker: conflictMarker;
          gutters = gutters.update({add: [marker.range(e.value.pos)]});
        }
      }
      if (e.is(removeGutterMarkerEffect)) {
        gutters = RangeSet.empty;
      }
    }
    return gutters;
  }
})
const pickerMarker = new (class extends GutterMarker {
  toDOM() {
    let pickerMarker = elt('div', PICKER_SYMBOL);
    pickerMarker.className = GUTTER_PICKER_CLASS;
    return pickerMarker;
  }
})();

 const conflictMarker = new (class extends GutterMarker {
  toDOM() {
    let conflictMarker = elt('div', CONFLICT_MARKER);
    conflictMarker.className = GUTTER_CONFLICT_CLASS;
    return conflictMarker;
  }
})();

const addLineChunkMappingEffect = StateEffect.define<{line: number, chunk: Chunk, type: String}>({
  map: (val, mapping) => ({line: mapping.mapPos(val.line), chunk: val.chunk, type: val.type})
})

const removeLineChunkMappingEffect = StateEffect.define<{type: String}>({
  map: (val) => ({type: val.type})
})

const pickerLineChunkMappingField = StateField.define<Map<number, Chunk>>({
  create:() => {
    return new Map();
  },
  update: (lineChunkMapping, transaction) => {
    let newLineChunkMapping = lineChunkMapping ;
    for (let e of transaction.effects) {
      if (e.is(addLineChunkMappingEffect) && e.value.type === 'picker') {
          newLineChunkMapping.set(e.value.line, e.value.chunk);
      }
    }
    return newLineChunkMapping;
  }
})

const conflictMarkerLineChunkMappingField = StateField.define<Map<number, Chunk>>({
  create:() => {
    return new Map();
  },
  update: (lineChunkMapping, transaction) => {
    let newLineChunkMapping = lineChunkMapping ;
    for (let e of transaction.effects) {
      if (e.is(addLineChunkMappingEffect) && e.value.type === 'conflict') {
          newLineChunkMapping.set(e.value.line, e.value.chunk);
      }
    }
    return newLineChunkMapping;
  }
})

/**
 *
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
    listener: Extension,
    mergeControlGutter: Extension,
    options: IMergeViewEditorConfiguration
  ) {
    this.model = model;
    this.type = type;
    let remoteValue = this.model.remote || '';
    this._remoteEditorWidget = new EditorWidget(remoteValue); // OPTIONS TO BE GIVEN
    this._remoteEditorWidget.editor.injectExtension([listener, mergeControlGutter, getCommonEditorExtensions()]);
    this.showDifferences = options.showDifferences !== false;
  }

  init(baseWidget: EditorWidget) {
    this.baseEditorWidget = baseWidget;
    let baseEditor = this.baseEditorWidget.cm;
    let remoteEditor = this.remoteEditorWidget.cm;
    this.lineChunks = this.model.getLineChunks();
    this.chunks = lineToNormalChunks(this.lineChunks);
    this.updateView(baseEditor, remoteEditor);
  }

  updateView( baseEditor: EditorView, remoteEditor: EditorView) {
    this.clearHighlighting(
      remoteEditor,
      this.model.additions,
      this.chunks,
      DIFF_OP.DIFF_INSERT
    );

    this.clearHighlighting(
      baseEditor,
      this.model.deletions,
      this.chunks,
      DIFF_OP.DIFF_DELETE
    );

    this.updateHighlighting(
      remoteEditor,
      this.model.additions,
      this.chunks,
      DIFF_OP.DIFF_INSERT
    );

    this.updateHighlighting(
      baseEditor,
      this.model.deletions,
      this.chunks,
      DIFF_OP.DIFF_DELETE
    );

    this.syncScroll(baseEditor, remoteEditor);
    this.syncScroll(remoteEditor, baseEditor);
  }
    syncModel() {
      if (!this.modelInvalid()) {
        return;
      }
      let editor = this.remoteEditorWidget.cm;
      let updatedLineChunks = this.model.getLineChunks();
      let updatedChunks = lineToNormalChunks(updatedLineChunks);
      if (this.model.remote === editor.state.doc.toString()) {
        // Nothing to do except update chunks
        this.lineChunks = updatedLineChunks;
        this.chunks = updatedChunks;
        return;
      }
      let cursor = editor.state.selection.main.head
      let newLines = splitLines(this.model.remote!);
      editor.dispatch({
        changes: {from: 0, to: editor.state.doc.length, insert: newLines.slice(0, newLines.length).join('')}
      });
      this.remoteEditorWidget.cm.dispatch({selection: {anchor: cursor}})
      this.lineChunks = updatedLineChunks;
      this.chunks = updatedChunks;
  }

  buildGap(): HTMLElement {
    let lock = (this.lockButton = elt('div', undefined, 'cm-merge-scrolllock'));
    lock.title = 'Toggle locked scrolling';
    let lockWrap = elt('div', [lock], 'cm-merge-scrolllock-wrap');
    lock.innerHTML = '\u21db&nbsp;&nbsp;\u21da';
    lock.addEventListener("scroll", (event) => {
       this.setScrollLock(!this.lockScroll);
      });
    return (this.gap = elt('div', [lockWrap], 'cm-merge-gap'));
  }

  setScrollLock(val: boolean, action?: boolean) {
    this.lockScroll = val;
    if (val && action !== false) {
      this.syncScroll(this.baseEditorWidget.cm, this.remoteEditorWidget.cm);
    }
    if (this.lockButton) {
      this.lockButton.innerHTML = val ? '\u21db\u21da' : '\u21db&nbsp;&nbsp;\u21da';
    }
  }

  protected modelInvalid(): boolean {
    return this.model instanceof DecisionStringDiffModel &&
            this.model.invalid;
  }

 /**
   * Sync scrolling between base and own editors. `type` is used to indicate
   * which editor is the source, and which editor is the destination of the sync.
   */
  protected syncScroll (srcEditor: EditorView, destEditor: EditorView): void {
    if (this.modelInvalid()) {
      return;
    }
    let srcScroller = srcEditor.scrollDOM;
    let destScroller = destEditor.scrollDOM;
    srcScroller.addEventListener("scroll", (event) => {
      window.requestAnimationFrame(function() {destScroller.scrollLeft = srcScroller.scrollLeft;})
    });
    return;
  }

  private getDecorationKey(sources: ChunkSource[]): string {
    let s: string = this.type;
    let res: string = s;
    if (this.type === 'merge') {
      s = sources[0].action;
      res = s + 'Merge'
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

private createGutterEffects (editor: EditorView, chunk: Chunk, pos: number, on: true, type: string) {
  let effects: StateEffect<unknown>[] = [];

  let gutterEffect = addGutterMarkerEffect.of({
    pos: pos,
    on: on,
    type: type
  })
  effects.push(gutterEffect);

  let line: number = offsetToPos(editor.state.doc, pos).line;
  let mappingEffect = addLineChunkMappingEffect.of({
    line: line,
    chunk: chunk,
    type: type
  });
  effects.push(mappingEffect);
  return effects;
}

/* Add line backgrounds and gutter markers effects*/
  private buildLineEffects(editor: EditorView, chunkArray: Chunk[]) {
    let effects: StateEffect<unknown>[] = [];
    let isbaseEditor = editor === this.baseEditorWidget.cm;
    for (let chunk of chunkArray) {
      let sources: ChunkSource[] = chunk.sources;
      let decorationKey = this.getDecorationKey(sources);
      let conflict = this.getConflictState(sources);
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

        effects.push(addHighlightEffect.of({
          from: startingOffset,
          to: startingOffset,
          highlightType: 'chunk',
          decorationKey: decorationKey
        }));

        if (conflict) {
          effects.push(addHighlightEffect.of({
            from: startingOffset,
            to: startingOffset,
            highlightType: 'conflict',
            decorationKey: decorationKey
          }));

        }
        if (i === chunkFirstLine) {
          effects.push(addHighlightEffect.of({
            from: startingOffset,
            to: startingOffset,
            highlightType: 'start',
            decorationKey: decorationKey
          }));

         if (!decorationKey.includes('Merge')) {
            // For all editors except merge editor, add a picker button
            effects = effects.concat(this.createGutterEffects(editor, chunk, startingOffset, true, 'picker'));
          } else if (editor === this.baseEditorWidget.cm) {
           for (let s of sources) {
              if (s.decision.action === 'custom' &&
                  !hasEntries(s.decision.localDiff) &&
                  !hasEntries(s.decision.remoteDiff)) {

                // We have a custom decision, add picker on base only!*/
                effects = effects.concat(this.createGutterEffects(editor, chunk, startingOffset, true, 'picker'));
              }
            }
          } else if (conflict && editor === this.remoteEditorWidget.cm) {
            effects = effects.concat(this.createGutterEffects(editor, chunk, startingOffset, true, 'conflict'));
          }
        }
        if (i === chunkLastLine - 1) {
          effects.push(addHighlightEffect.of({
            from: startingOffset,
            to: startingOffset,
            highlightType: 'end',
            decorationKey: decorationKey
          }));
        }
      }
      if (chunkFirstLine === chunkLastLine) {
        const startingOffset = posToOffset(editor.state.doc, { line: chunkFirstLine, column: 0 });
        effects.push(addHighlightEffect.of({
          from: startingOffset,
          to: startingOffset,
          highlightType: 'endEmpty',
          decorationKey: decorationKey
        }));
        if (!decorationKey.includes('Merge')) {
          effects = effects.concat(this.createGutterEffects(editor, chunk, chunkLastLine, true, 'picker'));

        } else if (conflict) {
          effects = effects.concat(this.createGutterEffects(editor, chunk, startingOffset, true, 'picker'));
        }
      }
    }
    return effects;
  }

  private clearLineEffects(editor: EditorView, chunkArray: Chunk[]) {
    let effects: StateEffect<unknown>[] = [];

    for (let chunk of chunkArray) {
      let sources: ChunkSource[] = chunk.sources;
      let decorationKey = this.getDecorationKey(sources);
      effects.push(removeHighlightEffect.of({highlightType: 'chunk', decorationKey: decorationKey}));
      effects.push(removeHighlightEffect.of({highlightType: 'conflict', decorationKey: decorationKey}));
      effects.push(removeHighlightEffect.of({highlightType: 'start', decorationKey: decorationKey}));
      effects.push(removeHighlightEffect.of({highlightType: 'end', decorationKey: decorationKey}));
    }
    if (editor !== this.baseEditorWidget.cm) {
      effects.push(removeGutterMarkerEffect.of({type: 'all' }));
      effects.push(removeLineChunkMappingEffect.of({type: 'picker'}));
      effects.push(removeLineChunkMappingEffect.of({type: 'conflict'}));
    }
    return effects;
  }

  private buildCharacterHighlighting(
    editor: EditorView,
    diffRanges: DiffRangePos[],
    markType: DIFF_OP
  ) {
    let effects: StateEffect<unknown>[] = [];
    let sources: ChunkSource[] = [];
    if (markType === DIFF_OP.DIFF_INSERT || markType === DIFF_OP.DIFF_DELETE) {
      let highlightType: string = markType === DIFF_OP.DIFF_DELETE ? 'deleted' : 'inserted';

      for (let r of diffRanges) {
        if (r.source !== undefined) {
          sources.push(r.source);
        }
        let decorationKey = this.getDecorationKey(sources);
        let startingOffset = posToOffset(editor.state.doc, {
          line: r.from.line,
          column: r.from.column
        });
        let endingOffset = posToOffset(editor.state.doc, {
          line: r.to.line,
          column: r.to.column
        });
        effects.push(addHighlightEffect.of({
          from: startingOffset,
          to: endingOffset,
          highlightType: highlightType,
          decorationKey: decorationKey
        }));
      }
    }
    return effects;
  }

  private clearCharacterHighlighting(
    editor: EditorView,
    diffRanges: DiffRangePos[],
    markType: DIFF_OP
  ) {
    let effects: StateEffect<unknown>[] = [];
    let sources: ChunkSource[] = [];
    if (markType === DIFF_OP.DIFF_INSERT || markType === DIFF_OP.DIFF_DELETE) {
      let highlightType: string = markType === DIFF_OP.DIFF_DELETE ? 'deleted' : 'inserted';
      for (let r of diffRanges) {
        if (r.source !== undefined) {
          sources.push(r.source);
        }
        let decorationKey = this.getDecorationKey(sources);
        effects.push(removeHighlightEffect.of({highlightType: highlightType, decorationKey: decorationKey}));
      }
    }
    return effects;
  }

  protected updateHighlighting(
    editor: EditorView,
    diffRanges: DiffRangePos[],
    chunkArray: Chunk[],
    type: DIFF_OP
  ) {
    let self = this;
    let LineHighlightEffects: StateEffect<unknown>[] =
      self.buildLineEffects(editor, chunkArray);
    let MarkHighlightEffects: StateEffect<unknown>[] =
      self.buildCharacterHighlighting(editor, diffRanges, type);
    let effects: StateEffect<unknown>[] =
      LineHighlightEffects.concat(MarkHighlightEffects);
    editor.dispatch({ effects });
  }

  protected clearHighlighting(
    editor: EditorView,
    diffRanges: DiffRangePos[],
    chunkArray: Chunk[],
    type: DIFF_OP
  ) {
    let self = this;
    let clearLineEffects: StateEffect<unknown>[] =
      self.clearLineEffects(editor, chunkArray);
    let clearCharacterHighlightEffects: StateEffect<unknown>[] =
      self.clearCharacterHighlighting(editor, diffRanges, type);
    let effects: StateEffect<unknown>[] =
      clearLineEffects.concat(clearCharacterHighlightEffects);
    editor.dispatch({ effects });
  }

  get remoteEditorWidget(): EditorWidget {
    return this._remoteEditorWidget;
  }

  baseEditorWidget: EditorWidget;
  private _remoteEditorWidget: EditorWidget;
  model: IStringDiffModel;
  type: string;
  showDifferences: boolean;
  chunks: Chunk[];
  lineChunks: Chunk[];
  gap: HTMLElement;
  lockScroll: boolean;
  protected lockButton: HTMLElement;
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
    if (linesToAlign.length > 0 &&
        linesToAlign[linesToAlign.length - 1][0] === lines[0]) {
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
        let lines = [chunk.baseTo,
                     getMatchingEditLineLC(chunk, dv.lineChunks)];
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
  console.log('Lines to align:', linesToAlign);
  return linesToAlign;
}
export interface IMergeViewEditorConfiguration
  extends LegacyCodeMirror.EditorConfiguration {

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
    super()
    this.options = options;
    this.measuring = -1;
    let remote = options.remote;
    let local = options.local || null;
    let merged = options.merged || null;
    let left: DiffView | null = (this.left = null);
    let right: DiffView | null = (this.right = null);
    let merge: DiffView | null = (this.merge = null);
    this.diffViews = [];
    let main = options.remote || options.merged;
    if (!main) {
      throw new Error('Either remote or merged model needs to be specified!');
    }
    options.value = main.base !== null ? main.base : main.remote;
    options.lineNumbers = options.lineNumbers !== false;
    // Whether merge view should be readonly
    let readOnly = options.readOnly;
    // For all others:
    options.readOnly = true;
    this.aligning = true;

    // listener extension to track for changes in the editorView
    const listener = EditorView.updateListener.of(update => {
      if (this.measuring < 0 && (/*update.heightChanged || */update.viewportChanged)
      && !update.transactions.some(tr => tr.effects.some(e => e.is(replacePaddingWidgetEffect)))) {
        this.alignViews();
      }
    });
    // mergeControlGutter to set the gutter in a given editor and the mousedown events for picker markers
    const mergeControlGutter = [
      gutterMarkerField,
      gutter({
        class: "cm-gutter",
        markers: editor => editor.state.field(gutterMarkerField),
        initialSpacer: () => pickerMarker,
        domEventHandlers: {
          mousedown: (editor, line) => {
            this.onGutterClick(editor, line);
            return true;
          }
        }
      })
    ]

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

    let dvOptions = options; // as CodeMirror.MergeView.MergeViewEditorConfiguration;

    if (merged) {
      //options.gutters = [GUTTER_CONFLICT_CLASS, GUTTER_PICKER_CLASS];
      if (options.lineWrap === undefined) {
        // Turn off linewrapping for merge view by default, keep for diff
        options.lineWrap = false;
      }
    }
    this.base = new EditorWidget(options.value); /*options to be given*/
    this.base.editor.injectExtension([listener, mergeControlGutter, getCommonEditorExtensions()]);
    /******************************Merge******************************** */
    if (merged) {
      this.gridPanel = new Panel();
      this.addWidget(this.gridPanel);
      this.gridPanel.addClass('cm-merge-grid-panel');
      let showBase = options.showBase !== false;

      if (!showBase) {
        this.base.node.style.display = 'hidden';
      }

      let leftWidget: Widget;
      if (!local || local.remote === null) {
        // Local value was deleted
        left = this.left = null;
        leftWidget = new Widget({
          node: elt('div', 'Value missing', 'jp-mod-missing')
        });
      } else {
        left = this.left = new DiffView(
          local,
          'left',
          listener,
          mergeControlGutter,
          copyObj(dvOptions)
        );
        this.diffViews.push(left);
        leftWidget = left.remoteEditorWidget;

      }
      this.gridPanel.addWidget(leftWidget);
      leftWidget.addClass('cm-merge-left-editor');

      if (showBase) {
        this.gridPanel.addWidget(this.base);
        this.base.addClass('cm-central-editor');
      }

      let rightWidget: Widget;
      if (!remote || remote.remote === null) {
        // Remote value was deleted
        right = this.right = null;
        rightWidget = new Widget({
          node: elt('div', 'Value missing', 'jp-mod-missing')
        });
      } else {
        right = this.right = new DiffView(
          remote,
          'right',
          listener,
          mergeControlGutter,
          copyObj(dvOptions)
        );
        this.diffViews.push(right);
        rightWidget = right.remoteEditorWidget;
      }
      this.gridPanel.addWidget(rightWidget);
      rightWidget.addClass('cm-merge-right-editor');

      merge = this.merge = new DiffView(
        merged,
        'merge',
        listener,
        mergeControlGutter,
        copyObj({ readOnly }, copyObj(dvOptions))
      );
      this.diffViews.push(merge);
      let mergeWidget = merge.remoteEditorWidget;
      this.gridPanel.addWidget(mergeWidget);
      mergeWidget.addClass('cm-merge-editor');
    /******************************Diff******************************** */
    } else if (remote) {
      this.gridPanel = new Panel();
      this.addWidget(this.gridPanel);
      this.gridPanel.addClass('cm-diff-grid-panel');
      // If in place for type guard
      this.gridPanel.addWidget(this.base);
      this.base.addClass('cm-diff-left-editor');
      if (remote.unchanged || remote.added || remote.deleted) {
        if (remote.unchanged) {
          this.base.addClass('cm-merge-pane-unchanged');
        } else if (remote.added) {
          this.base.addClass('cm-merge-pane-added');
        } else if (remote.deleted) {
          this.base.addClass('cm-merge-pane-deleted');
        }
      } else {
        right = this.right = new DiffView(
          remote,
          'right',
          listener,
          mergeControlGutter,
          dvOptions
        );
        this.diffViews.push(right);
        let rightWidget = right.remoteEditorWidget;
        rightWidget.addClass('cm-diff-right-editor');
        this.addWidget(new Widget({node: right.buildGap()}));
        this.gridPanel.addWidget(rightWidget);
      }
    }

    for (let dv of [left, right, merge]) {
      if (dv) {
        dv.init(this.base);
      }
    }
    this.aligning = false;
    this.scheduleAlignViews();
  }
  alignViews() {
    let lineHeight = this.base.cm.defaultLineHeight;
    if (this.aligning) {
      return;
    }
    this.aligning = true;
    // Find matching lines
    let linesToAlign = findAlignedLines(this.diffViews);

    // Function modifying DOM to perform alignment:
    let self: MergeView = this;
    let editors: EditorView[] = [self.base.cm];
    let builders: RangeSetBuilder<Decoration>[] = [];
      for (let dv of self.diffViews) {
        editors.push(dv.remoteEditorWidget.cm);
      }
      for (let i = 0; i < editors.length; i++) {
        builders.push(new RangeSetBuilder<Decoration>());
      }

    let sumDeltas = new Array(editors.length).fill(0);
    let nLines = editors.map(editor => editor.state.doc.lines);

    for (let alignment_ of linesToAlign) {
      let alignment = alignment_.slice(0, 3)
      let lastLine = Math.max(...alignment);
      let lineDeltas = alignment.map((line, i) => lastLine - line - sumDeltas[i]);
      // If some spacers will be before the current line, it means all other editors
      // must add a spacer.
      let minDelta = Math.min(...lineDeltas);
      let correctedDeltas = lineDeltas.map(line => line - minDelta);

      correctedDeltas.forEach((delta, i) => {
        let side = -1;
        let line = alignment[i] - 1;

        if (delta > 0 && line < nLines[i]) {
          sumDeltas[i] += delta;

          let offset = posToOffset(editors[i].state.doc, {
            line,
            column: 0
          });

          builders[i].add(offset, offset, Decoration.widget({
            widget: new PaddingWidget(delta * lineHeight),
            block: true,
            side
          }));
        }
      });
    }

    // Last spacer
    let totalHeight = nLines.map((line, i) => line + sumDeltas[i]);
    let maxHeight = Math.max(...totalHeight);
    totalHeight.slice(0, 3).forEach((line, i) => {
      if(maxHeight > line) {
        let end = editors[i].state.doc.length;
        let delta = maxHeight - line;
        sumDeltas[i] += delta;
        builders[i].add(end, end, Decoration.widget({
          widget: new PaddingWidget(delta * lineHeight),
          block: true,
          side: 1
        }));
      }
    })


    for (let i = 0; i < editors.length; i++) {
        let decoSet: DecorationSet = builders[i].finish();
        if (!RangeSet.eq([decoSet], [editors[i].state.field(paddingWidgetField)])) {
          editors[i].dispatch({ effects: replacePaddingWidgetEffect.of(decoSet) });
        }
      }

    this.aligning = false;
    };

    scheduleAlignViews() {
      if (this.measuring < 0) {
        let win = (this.gridPanel.node.ownerDocument.defaultView || window)
        this.measuring = win.requestAnimationFrame(() => {
          this.measuring = -1;
          this.alignViews();
        })
      }
    }

  protected onGutterClick(editor: EditorView, line: BlockInfo): boolean {
    let effects: StateEffect<unknown>[] = [];
    let offset: number = line.from;
    let gutterMarkerline: number = offsetToPos(editor.state.doc, offset).line;
    let isPicker: boolean = editor!=this.merge?.remoteEditorWidget.cm;

    if (isPicker) {
      let pickerLineChunksMapping = editor.state.field(pickerLineChunkMappingField);
      let chunk: Chunk = pickerLineChunksMapping.get(gutterMarkerline)!;
      let sources: ChunkSource[] = chunk.sources;

      if (!(editor == this.base.cm)) {
        for (let source of sources) {
          source.decision.action = source.action;
        }
      } else if (this.merge && editor === this.base.cm) {
        for (let source of sources) {
          source.decision.action = 'base';
        }
      }
      for (let i=sources.length - 1; i >= 0; --i) {
        let source = sources[i];
        if (this.merge && hasEntries(source.decision.customDiff)) {
          // Custom diffs are cleared on pick,
          // as there is no way to re-pick them
          source.decision.customDiff = [];
        }
      }
        if (sources.length === 0) {
        // All decisions empty, remove picker
        // In these cases, there should only be one picker, on base
        // so simply remove the one we have here
      }
      effects.push(addGutterMarkerEffect.of({
        pos: line.from,
        on: false,
        type: 'picker'
      }))
    } else  { // conflict picker
      let conflictLineChunksMapping = editor.state.field(conflictMarkerLineChunkMappingField);
      let chunk: Chunk = conflictLineChunksMapping.get(gutterMarkerline)!;
      let sources: ChunkSource[] = chunk.sources;

      for (let source of sources) {
        if (editor !== this.base.cm) {
          source.decision.conflict = false;
        }
      }
    }

    editor.dispatch({effects: effects});
    this.updateDiffModels();
    this.updateDiffViews();
    this.alignViews();
    return true;
  }

  private updateDiffModels() {
    for (let dv of this.diffViews) {
      if (dv.model instanceof DecisionStringDiffModel) {
        dv.model.invalidate();
      }
      dv.syncModel();
    }
  }
  private updateDiffViews() {
     /* before updating the diffViews, baseEditor needs to be cleared from its pickers*/
    this.clearBaseEditorPickers();
    for (let dv of this.diffViews) {
      dv.updateView(dv.baseEditorWidget.cm, dv.remoteEditorWidget.cm);
    }
  }

  private clearBaseEditorPickers() {
    /* baseEditor is cumulating pickers from different diffViews*/
    /*  since this editor is common to the 3 diffviews */
    let effects: StateEffect<unknown>[] = [];
    effects.push(removeGutterMarkerEffect.of({type: 'all'}));
    effects.push(removeLineChunkMappingEffect.of({type: "picker"}));
    this.base.cm.dispatch({effects});
  }

  gridPanel: Panel;
  subPanel1: Panel;
  subPanel2: Panel;
  left: DiffView | null;
  right: DiffView | null;
  merge: DiffView | null;
  base: EditorWidget;
  options: any;
  diffViews: DiffView[];
  aligning: boolean;
  measuring: number;
}
// General utilities
function elt(
  tag: string,
  content?: string | HTMLElement[] | null,
  className?: string | null,
  style?: string | null
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
