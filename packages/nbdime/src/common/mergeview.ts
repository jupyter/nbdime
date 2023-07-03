// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.

// This code is based on the CodeMirror mergeview.js source:
// CodeMirror, copyright (c) by Marijn Haverbeke and others
// Distributed under an MIT license: http://codemirror.net/LICENSE

'use strict';

import { Widget, Panel /*SplitPanel*/ } from '@lumino/widgets';

import type { IStringDiffModel } from '../diff/model';

/*import {
  DecisionStringDiffModel
} from '../merge/model';*/

import type { DiffRangePos } from '../diff/range';

import { ChunkSource, Chunk, lineToNormalChunks } from '../chunking';

import { EditorWidget } from './editor';

import { valueIn, /*hasEntries*/ copyObj } from './util';


/* import {
  NotifyUserError
} from './exceptions'; */

/*import {
  python
} from '@codemirror/lang-python';
*/

import { python } from "@codemirror/lang-python";

import {
  Extension,
  StateEffect,
  StateField,
  ChangeDesc,
  /*RangeSet,*/
  /*Line,*/
  /*Text,*/
  Range
} from '@codemirror/state';

import {
  EditorView,
  lineNumbers,
  ViewPlugin,
  ViewUpdate,
  Decoration,
  DecorationSet,
  /*keymap,*/
  WidgetType
} from '@codemirror/view';

import { LegacyCodeMirror } from '../legacy_codemirror/cmconfig';
//const PICKER_SYMBOL = '\u27ad';

//const CONFLICT_MARKER = '\u26A0'; // '\u2757'

/*export
type Marker = CodeMirror.LineHandle | CodeMirror.TextMarker;*/

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

/*const GUTTER_PICKER_CLASS = 'jp-Merge-gutter-picker';
const GUTTER_CONFLICT_CLASS = 'jp-Merge-gutter-conflict';*/

const CHUNK_CONFLICT_CLASS = 'jp-Merge-conflict';

/*const leftClasses: DiffClasses = { chunk: 'CodeMirror-merge-l-chunk',
          start: 'CodeMirror-merge-l-chunk-start',
          end: 'CodeMirror-merge-l-chunk-end',
          insert: 'CodeMirror-merge-l-inserted',
          del: 'CodeMirror-merge-l-deleted',
          connect: 'CodeMirror-merge-l-connect',
          gutter: 'CodeMirror-merge-l-gutter'};
const rightClasses: DiffClasses = { chunk: 'CodeMirror-merge-r-chunk',
          start: 'CodeMirror-merge-r-chunk-start',
          end: 'CodeMirror-merge-r-chunk-end',
          insert: 'CodeMirror-merge-r-inserted',
          del: 'CodeMirror-merge-r-deleted',
          connect: 'CodeMirror-merge-r-connect',
          gutter: 'CodeMirror-merge-r-gutter'};

/*const mergeClassPrefix: DiffClasses = {chunk: 'CodeMirror-merge-m-chunk',
          start: 'CodeMirror-merge-m-chunk-start',
          end: 'CodeMirror-merge-m-chunk-end',
          insert: 'CodeMirror-merge-m-inserted',
          del: 'CodeMirror-merge-m-deleted',
          connect: 'CodeMirror-merge-m-connect',
          gutter: 'CodeMirror-merge-m-gutter'};
*/

/************************ start decoration lines and marks*****************************/
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
const diffViewPlugin = ViewPlugin.fromClass(
  class {
    addDiffView(dv: DiffView): void {
      this.diffviews.push(dv);
    }
    update(update: ViewUpdate) {
      if (update.docChanged || update.viewportChanged) {
        //console.log('Update tracker');
        /*for (let dv of this.diffviews ) {
        dv.update();
      }*/
      }
    }
    private diffviews: DiffView[] = [];
  }
);

function getCommonEditorExtensions(): Extension {
  return [
    diffViewPlugin,
    lineNumbers(),
    HighlightField,
    PaddingWidgetField,
    python()
    /*decorationKeymap*/
  ];
}

function applyMapping({ from, to }: any, mapping: ChangeDesc) {
  const map: any = { from: mapping.mapPos(from), to: mapping.mapPos(to) };
  return map;
}
const addHighlight = StateEffect.define<{
  from: number;
  to: number;
  highlightType: string;
  decorationKey: string;
}>({
  map: applyMapping
});

const removeHighlight = StateEffect.define<{
  highlightType: string;
  decorationKey: string;
}>({
  map: applyMapping
});

const HighlightField = StateField.define<DecorationSet>({
  create() {
    return Decoration.none;
  },
  update(highlightRanges, transaction) {
    highlightRanges = highlightRanges.map(transaction.changes);
    for (let e of transaction.effects) {
      let decoration: Decoration;
      if (e.is(addHighlight)) {
        decoration = mergeViewDecorationDict[e.value.decorationKey][e.value.highlightType];
        highlightRanges = highlightRanges.update({
          add: [decoration.range(e.value.from, e.value.to)]
        });
        /*console.log('****************************')
        console.log(e.value.decorationKey);
        console.log(e.value.highlightType);
        console.log('spec:', decoration.spec.class);
        console.log('****************************')*/
      }
      if (e.is(removeHighlight)) {
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

/*function leftHighlightChunkSelection(view: EditorView) {
   let highlightType = 'chunk'
   let decorationKey = 'left';
    let effects: StateEffect<unknown>[] = view.state.selection.ranges
    .filter(r => !r.empty)
    .map(({ from }) => addHighlight.of({ from, to: from, highlightType, decorationKey }));
  view.dispatch({ effects });
  return true;
}

function rightHighlightChunkSelection(view: EditorView) {
   let highlightType = 'chunk'
   let decorationKey = 'right';
    let effects: StateEffect<unknown>[] = view.state.selection.ranges
    .filter(r => !r.empty)
    .map(({ from }) => addHighlight.of({ from, to: from, highlightType, decorationKey }));
  view.dispatch({ effects });
  return true;
}

function leftHighlightInsertSelection(view: EditorView) {
  let highlightType = 'inserted'
  let decorationKey = 'left';
   let effects: StateEffect<unknown>[] = view.state.selection.ranges
   .filter(r => !r.empty)
   .map(({ from, to }) => addHighlight.of({ from, to, highlightType, decorationKey }));
 view.dispatch({ effects });
 return true;
}

function rightHighlightInsertSelection(view: EditorView) {
  let highlightType = 'inserted'
  let decorationKey = 'right';
   let effects: StateEffect<unknown>[] = view.state.selection.ranges
   .filter(r => !r.empty)
   .map(({ from, to }) => addHighlight.of({ from, to, highlightType, decorationKey }));
 view.dispatch({ effects });
 return true;
}*/
/***********************start decoration widget and related statefield***********************************/
const addPaddingWidgetEffect = StateEffect.define<{ offset: number; size: number; above: boolean }>({
  map: ({ offset, size, above }, mapping) => ({
    offset: mapping.mapPos(offset),
    size,
    above
  })
});

const PaddingWidgetField = StateField.define<DecorationSet>({
  create: () => {
    return Decoration.none;
  },
  update: (paddingWidgetRanges, transaction) => {
    paddingWidgetRanges = paddingWidgetRanges.map(transaction.changes);
    for (let e of transaction.effects) {
      if (e.is(addPaddingWidgetEffect))
      paddingWidgetRanges = paddingWidgetRanges.update({
          add: [addPaddingWidget(e.value.offset, e.value.size, e.value.above)]
        });
    }
    return paddingWidgetRanges;
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

function posToOffset(doc: any, pos: any) {
  return doc.line(pos.line + 1).from + pos.ch;
}

/* function offsetToPos(doc, offset) {
  let line = doc.lineAt(offset)
  return {line: line.number - 1, ch: offset - line.from}
} */

function addPaddingWidget(
  pos: number,
  size: number,
  above: boolean
): Range<Decoration> {
  let deco = Decoration.widget({
    widget: new PaddingWidget(size),
    block: true,
    side: above? -1 : 1
  });
  return deco.range(pos);
}

/*function addLineWidgetFromUI(view: EditorView) {
  const cursor = view.state.selection.main.head;
  const line: Line = view.state.doc.lineAt(cursor);
  let effects: StateEffect<unknown>[] = [];
  effects.push(addLineWidgetEffect.of({line: line.number, size: 40}));
  view.dispatch({effects});
  return true;

}*/
/**************************end decoration widget and related statefield************************************************* */
/*const decorationKeymap = keymap.of([
  {
    key: 'Alt-u',
    preventDefault: true,
    run: leftHighlightChunkSelection
  },
  {
    key: 'Alt-v',
    preventDefault: true,
    run: leftHighlightInsertSelection
  },
  {
    key: 'Alt-w',
    preventDefault: true,
    run: rightHighlightChunkSelection
  },
  {
    key: 'Alt-x',
    preventDefault: true,
    run: rightHighlightInsertSelection
  },
  {
    key: 'Alt-h',
    preventDefault: true,
    run: addLineWidgetFromUI
  }],
)*/

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
  opts.collapseIdentical = true;
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
    updateCallback: (force?: boolean) => void,
    options: IMergeViewEditorConfiguration
  ) {
    this.model = model;
    this.type = type;
    this.updateCallback = updateCallback;
    //this.classes = type === 'left' ?
    //leftClasses : type === 'right' ? rightClasses : null;
    let remoteValue = this.model.remote || '';
    //this.remoteEditorWidget = new EditorWidget(remoteValue, copyObj({readOnly: !!options.readOnly}, options));
    this._remoteEditorWidget = new EditorWidget(remoteValue); // OPTIONS TO BE GIVEN
    this._remoteEditorWidget.editor.injectExtension(getCommonEditorExtensions());
    this.showDifferences = options.showDifferences !== false;
  }
  /*
init(base: CodeMirror.Editor) {
    this.baseEditor = base;
    (this.baseEditor.state.diffViews ||
     (this.baseEditor.state.diffViews = [])).push(this);
    this.remoteEditor.state.diffViews = [this];

    this.baseEditor.on('gutterClick', this.onGutterClick.bind(this));
    this.remoteEditor.on('gutterClick', this.onGutterClick.bind(this));

    this.lineChunks = this.model.getLineChunks();
    this.chunks = lineToNormalChunks(this.lineChunks);
    this.dealigned = false;

    this.forceUpdate = this.registerUpdate();
    this.setScrollLock(true, false);
    this.registerScroll();
  }
*/

  init(baseWidget: EditorWidget) {
    this.baseEditorWidget = baseWidget;
    const baseEditor = this.baseEditorWidget.cm;
    const remoteEditor = this.remoteEditorWidget.cm;
    const baseEditorPlugin = baseEditor.plugin(diffViewPlugin);
    const remoteEditorPlugin = remoteEditor.plugin(diffViewPlugin);
    baseEditorPlugin?.addDiffView(this);
    remoteEditorPlugin?.addDiffView(this);

    //this.baseEditor.on('gutterClick', this.onGutterClick.bind(this));
    //this.remoteEditor.on('gutterClick', this.onGutterClick.bind(this));

    this.lineChunks = this.model.getLineChunks();
    this.chunks = lineToNormalChunks(this.lineChunks);
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



    /*this.dealigned = false;

    this.forceUpdate = this.registerUpdate();

    this.setScrollLock(true, false);
    this.registerScroll();
    */
  }

  update() {}

  setShowDifferences(val: boolean) {
    /*
     val = val !== false;
    if (val !== this.showDifferences) {
      this.showDifferences = val;
      this.forceUpdate('full');
    }
    */
  }

  syncModel() {
    /*if (this.modelInvalid()) {
      let edit = this.remoteEditor;
      let updatedLineChunks = this.model.getLineChunks();
      let updatedChunks = lineToNormalChunks(updatedLineChunks);
      //if (this.model.remote === edit.getValue()) {//
      if (this.model.remote === edit.state.doc.toString) {
        // Nothing to do except update chunks
        this.lineChunks = updatedLineChunks;
        this.chunks = updatedChunks;
        return;
      }
      //let cursor = edit.getDoc().getCursor();
      let cursor = edit.state.selection.main.head
      let newLines = splitLines(this.model.remote!);
      //let start = edit.getDoc().firstLine();
      //let last = edit.getDoc().lastLine() + 1;
      let start = edit.state.doc.firstLine();
      let last = edit.state.doc.lastLine() + 1;
      let cumulativeOffset = 0;
      let end: number;
      let updatedEnd: number;
      // We want to replace contents of editor, but if we have collapsed regions
      // some lines have been optimized away. Carefully replace the relevant bits:
      for (let range of this.collapsedRanges) {
        let baseLine = range.line;
        end = getMatchingEditLine(baseLine, this.chunks);
        updatedEnd = getMatchingEditLine(baseLine, updatedChunks);
        let offset = updatedEnd - end;
        if (end !== start || offset !== 0) {
          //edit.getDoc().replaceRange(
          edit.state.doc.replaceRange(
            newLines.slice(start + cumulativeOffset, updatedEnd + cumulativeOffset - 1).join(''),
            //CodeMirror.Pos(start, 0),
            //CodeMirror.Pos(end - 1, 0),
            { line: start, column: 0 },
            { line: end - 1, column: 0 },
            'syncModel'
          );
        }
        cumulativeOffset += offset;
        start = end + range.size;
      }
      if (start < last) {
        // Only here if no collapsed ranges, replace full contents
        edit.getDoc().replaceRange(
          newLines.slice(start, newLines.length).join(''),
          CodeMirror.Pos(start, 0),
          CodeMirror.Pos(last, 0),
          'syncModel'
        );
      }
      this.remoteEditor.getDoc().setCursor(cursor);
      this.lineChunks = updatedLineChunks;
      this.chunks = updatedChunks;
    }
    */
  }

  buildGap(): HTMLElement {
    let lock = (this.lockButton = elt('div', undefined, 'cm-merge-scrolllock'));
    lock.title = 'Toggle locked scrolling';
    let lockWrap = elt('div', [lock], 'cm-merge-scrolllock-wrap');
    // TODO: plug listener
    lock.innerHTML = '\u21db&nbsp;&nbsp;\u21da';
    /*let self: DiffView = this;
    CodeMirror.on(lock, 'click', function() {
      self.setScrollLock(!self.lockScroll);
    });*/
    return (this.gap = elt('div', [lockWrap], 'cm-merge-gap'));
    //return (document.createElement("div"));
  }

  setScrollLock(val: boolean, action?: boolean) {
    /* this.lockScroll = val;
    if (val && action !== false) {
      this.syncScroll(EventDirection.OUTGOING);
    }
    if (this.lockButton) {
      this.lockButton.innerHTML = val ? '\u21db\u21da' : '\u21db&nbsp;&nbsp;\u21da';
    } */
  }

  protected registerUpdate() {
    /* let editMarkers: Marker[] = [];
    let origMarkers: Marker[] = [];
    let debounceChange: number;
    let self: DiffView = this;
    self.updating = false;
    self.updatingFast = false;

    function update(mode?: 'full') {
      self.updating = true;
      self.updatingFast = false;
      if (mode === 'full') {
        self.syncModel();
        if (self.classes === null) {
          clearMergeMarks(self.baseEditorWidget, editMarkers);
          clearMergeMarks(self.remoteEditor, origMarkers);
        } else {
          clearMarks(self.baseEditorWidget, editMarkers, self.classes);
          clearMarks(self.remoteEditor, origMarkers, self.classes);
        }
      }
      if (self.showDifferences) {
        self.updateMarks(
          self.remoteEditor, self.model.additions,
          editMarkers, DIFF_OP.DIFF_INSERT);
        self.updateMarks(
          self.baseEditorWidget, self.model.deletions,
          origMarkers, DIFF_OP.DIFF_DELETE);
      }

      self.updateCallback(true);
      checkSync(self.remoteEditor);
      self.updating = false;
    }
    function setDealign(fast: boolean | CodeMirror.Editor, diffViews: diffView[]) {
        let upd = false;
        for (let dv of self.baseEditorWidget.state.diffViews) {
          upd = upd || dv.updating;
        }
        if (upd) {
          return;
        }
        self.dealigned = true;
        set(fast === true);
    }
    function set(fast: boolean) {
      let upd = false;
      for (let dv of self.baseEditorWidget.state.diffViews) {
        upd = upd || dv.updating || dv.updatingFast;
      }
      if (upd) {
        return;
      }
      clearTimeout(debounceChange);
      if (fast === true) {
        self.updatingFast = true;
      }
      debounceChange = window.setTimeout(update, fast === true ? 20 : 250);
    }
    function change(_cm: CodeMirror.Editor, change: CodeMirror.EditorChange) {
      if (!(self.model instanceof DecisionStringDiffModel)) {
        // TODO: Throttle?
        self.lineChunks = self.model.getLineChunks();
        self.chunks = lineToNormalChunks(self.lineChunks);
      }
      // Update faster when a line was added/removed
      setDealign(change.text.length - 1 !== change.to.line - change.from.line);
    }
    function checkSync(cm: CodeMirror.Editor) {
      if (self.model.remote !== cm.getValue()) {
        throw new NotifyUserError(
          'CRITICAL: Merge editor out of sync with model! ' +
          'Double-check any saved merge output!');
      }
    }
    */
    /*this.baseEditorWidget.on('change', change);
    this.remoteEditor.on('change', change);
    this.baseEditorWidget.on('markerAdded', setDealign);
    this.baseEditorWidget.on('markerCleared', setDealign);
    this.remoteEditor.on('markerAdded', setDealign);
    this.remoteEditor.on('markerCleared', setDealign);
    this.baseEditorWidget.on('viewportChange', function() { set(false); });
    this.remoteEditor.on('viewportChange', function() { set(false); });
    update();*/

    return () => {};
  }

  protected modelInvalid(): boolean {
    /* return this.model instanceof DecisionStringDiffModel &&
            this.model.invalid; */
    return false;
  }

  /*protected onGutterClick(instance: CodeMirror.Editor, line: number, gutter: string, clickEvent: Event): void {
    if ((clickEvent as MouseEvent).button !== 0) {
      // Only care about left clicks
      return;
    }
    let li = instance.lineInfo(line);
    if (!li.gutterMarkers || !li.gutterMarkers.hasOwnProperty(gutter)) {
      return;
    }
    let node = li.gutterMarkers[gutter];
    if (node && node.sources) {
      let ss = node.sources as ChunkSource[];
      if (gutter === GUTTER_PICKER_CLASS) {
        if (instance === this.remoteEditor) {
          for (let s of ss) {
            s.decision.action = s.action;
          }
        } else if (this.type === 'merge' && instance === this.baseEditorWidget) {
          for (let s of ss) {
            s.decision.action = 'base';
          }
        }
        for (let i=ss.length - 1; i >= 0; --i) {
          let s = ss[i];
          if (this.type === 'merge' && hasEntries(s.decision.customDiff)) {
            // Custom diffs are cleared on pick,
            // as there is no way to re-pick them
            s.decision.customDiff = [];
          }
        }
        if (ss.length === 0) {
          // All decisions empty, remove picker
          // In these cases, there should only be one picker, on base
          // so simply remove the one we have here
          instance.setGutterMarker(line, GUTTER_PICKER_CLASS, null);
        }
      } else if (gutter === GUTTER_CONFLICT_CLASS) {
        for (let s of ss) {
          s.decision.conflict = false;
        }
      }
      for (let dv of this.baseEditorWidget.state.diffViews as DiffView[]) {
        if (dv.model instanceof DecisionStringDiffModel) {
          dv.model.invalidate();
        }
        dv.forceUpdate('full');
      }
    }
  }*/

  protected registerScroll(): void {
    /* let self = this;
    this.baseEditorWidget.on('scroll', function() {
      self.syncScroll(EventDirection.OUTGOING);
    });
    this.remoteEditor.on('scroll', function() {
      self.syncScroll(EventDirection.INCOMING);
    }); */
  }

  /**
   * Sync scrolling between base and own editors. `type` is used to indicate
   * which editor is the source, and which editor is the destination of the sync.
   */
  protected syncScroll(type: EventDirection): void {
    /* if (this.modelInvalid()) {
      return;
    }
    if (!this.lockScroll) {
      return;
    }
    // editor: What triggered event, other: What needs to be synced
    let editor: CodeMirror.Editor;
    let other: CodeMirror.Editor;
    if (type === EventDirection.OUTGOING) {
      editor = this.baseEditorWidget;
      other = this.remoteEditor;
    } else {
      editor = this.remoteEditor;
      other = this.baseEditorWidget;
    }

    if (editor.state.scrollSetBy === this) {
      editor.state.scrollSetBy = null;
      return;
    }

    // Position to update to
    other.state.scrollPosition = editor.getScrollInfo();

    // If ticking, we already have a scroll queued
    if (other.state.scrollTicking) {
      return;
    }

    let sInfo = other.getScrollInfo();
    // Don't queue an event if already synced.
    if (other.state.scrollPosition.top === sInfo.top &&
        other.state.scrollPosition.left === sInfo.left) {
      return;
    }
    // Throttle by requestAnimationFrame().
    // If event is outgoing, this will lead to a one frame delay of other DiffViews
    let self = this;
    window.requestAnimationFrame(function() {
      other.scrollTo(other.state.scrollPosition.left, other.state.scrollPosition.top);
      other.state.scrollTicking = false;
      other.state.scrollSetBy = self;
    });
    other.state.scrollTicking = true;
    return; */
  }

  /*protected updateMarks(editor: EditorView, diff: DiffRangePos[],
                        markers: Marker[], type: DIFF_OP) {
    let classes: DiffClasses;
    if (this.classes === null) {
      // Only store prefixes here, will be completed later
      classes = copyObj(mergeClassPrefix);
    } else {
      classes = this.classes;
    }

    let self = this;
    function markChunk(editor: EditorView, from: number, to: number,
                       sources: ChunkSource[]) {
      if (self.classes === null && sources.length > 0) {
        // Complete merge class prefixes here
        classes = copyObj(mergeClassPrefix);
        // First, figure out 'action' state of chunk
        let s: string = sources[0].action;
        if (sources.length > 1) {
          for (let si of sources.slice(1)) {
            if (si.action !== s) {
              s = 'mixed';
              break;
            }
          }
        }
        for (let k of Object.keys(classes)) {
          classes[k] += '-' + s;
        }
      }
      // Next, figure out conflict state
      let conflict = false;
      if (sources.length > 0) {
        for (let s of sources) {
          if (s.decision.conflict) {
            conflict = true;
            break;
          }
        }
      }

      for (let i = from; i < to; ++i) {
        let line = editor.addLineClass(i, 'background', classes.chunk);
        if (conflict) {
          editor.addLineClass(line, 'background', CHUNK_CONFLICT_CLASS);
        }
        if (i === from) {
          editor.addLineClass(line, 'background', classes.start);
          if (self.type !== 'merge') {
            // For all editors except merge editor, add a picker button
            let picker = elt('div', PICKER_SYMBOL, classes.gutter);
            (picker as any).sources = sources;
            picker.classList.add(GUTTER_PICKER_CLASS);
            editor.setGutterMarker(line, GUTTER_PICKER_CLASS, picker);
          } else if (editor === self.baseEditorWidget) {
            for (let s of sources) {
              if (s.decision.action === 'custom' &&
                  !hasEntries(s.decision.localDiff) &&
                  !hasEntries(s.decision.remoteDiff)) {
                // We have a custom decision, add picker on base only!
                let picker = elt('div', PICKER_SYMBOL, classes.gutter);
                (picker as any).sources = sources;
                picker.classList.add(GUTTER_PICKER_CLASS);
                editor.setGutterMarker(line, GUTTER_PICKER_CLASS, picker);
              }
            }
          } else if (conflict && editor === self.remoteEditor) {
            // Add conflict markers on editor, if conflicted
            let conflictMarker = elt('div', CONFLICT_MARKER, '');
            (conflictMarker as any).sources = sources;
            conflictMarker.classList.add(GUTTER_CONFLICT_CLASS);
            editor.setGutterMarker(line, GUTTER_CONFLICT_CLASS, conflictMarker);
          }
        }
        if (i === to - 1) {
          editor.addLineClass(line, 'background', classes.end);
        }
        markers.push(line);
      }
      // When the chunk is empty, make sure a horizontal line shows up
      if (from === to) {
        let line = editor.addLineClass(from, 'background', classes.start);
        if (self.type !== 'merge') {
          let picker = elt('div', PICKER_SYMBOL, classes.gutter);
          (picker as any).sources = sources;
          picker.classList.add(GUTTER_PICKER_CLASS);
          editor.setGutterMarker(line, GUTTER_PICKER_CLASS, picker);
        } else if (conflict) {
          // Add conflict markers on editor, if conflicted
          let conflictMarker = elt('div', CONFLICT_MARKER, '');
          (conflictMarker as any).sources = sources;
          conflictMarker.classList.add(GUTTER_CONFLICT_CLASS);
          editor.setGutterMarker(line, GUTTER_CONFLICT_CLASS, conflictMarker);
        }
        editor.addLineClass(line, 'background', classes.end + '-empty');
        markers.push(line);
      }
    }
    let cls = type === DIFF_OP.DIFF_DELETE ? classes.del : classes.insert;
    editor.operation(function() {
      let edit = editor === self.baseEditorWidget;
      if (self.classes) {
        clearMarks(editor, markers, classes);
      } else {
        clearMergeMarks(editor, markers);
      }
      highlightChars(editor, diff, markers, cls);
      for (let c of self.chunks) {
        if (edit) {
          markChunk(editor, c.baseFrom, c.baseTo, c.sources);
        } else {
          markChunk(editor, c.remoteFrom, c.remoteTo, c.sources);
        }
      }
    });
  }*/

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

  private createAddHighlightEffect(
    highlightType: string,
    decorationKey: string,
    startingOffset: number,
    endingOffset?: number
  ) {
    const effect = addHighlight.of({
      from: startingOffset,
      to: endingOffset ?? startingOffset,
      highlightType: highlightType,
      decorationKey: decorationKey
    });
    return effect;
  }

  private createClearHighlightEffect(
    highlightType: string,
    decorationKey: string
  ) {
    const effect = removeHighlight.of({
      highlightType: highlightType,
      decorationKey: decorationKey
    });
    return effect;
  }

  private buildLineHighlighting(editor: EditorView, chunkArray: Chunk[]) {
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
        const pos: any = { line: i, ch: 0 };
        const startingOffset = posToOffset(editor.state.doc, pos);
        effects.push(
          this.createAddHighlightEffect('chunk', decorationKey, startingOffset)
        );
        if (conflict) {
          effects.push(
            this.createAddHighlightEffect('conflict', decorationKey, startingOffset)
          );
        }
        if (i === chunkFirstLine) {
          effects.push(
            this.createAddHighlightEffect('start', decorationKey, startingOffset)
          );
        }
        if (i === chunkLastLine - 1) {
          effects.push(this.createAddHighlightEffect('end', decorationKey, startingOffset));
        }
      }
      if (chunkFirstLine === chunkLastLine) {
        const startingOffset = posToOffset(editor.state.doc, { line: chunkFirstLine, ch: 0 });
        effects.push(
          this.createAddHighlightEffect('endEmpty', decorationKey, startingOffset)
        );
      }
    }
    return effects;
  }

  private clearLineHighlighting(editor: EditorView, chunkArray: Chunk[]) {
    let effects: StateEffect<unknown>[] = [];

    for (let chunk of chunkArray) {
      let sources: ChunkSource[] = chunk.sources;
      let decorationKey = this.getDecorationKey(sources);
      effects.push(this.createClearHighlightEffect('chunk', decorationKey));
      effects.push(this.createClearHighlightEffect('conflict', decorationKey));
      effects.push(this.createClearHighlightEffect('start', decorationKey));
      effects.push(this.createClearHighlightEffect('end', decorationKey,));
      }

    return effects;
  }

  private buildMarkHighlighting(
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
          ch: r.from.column
        });
        let endingOffset = posToOffset(editor.state.doc, {
          line: r.to.line,
          ch: r.to.column
        });
        effects.push(
          this.createAddHighlightEffect(
            highlightType,
            decorationKey,
            startingOffset,
            endingOffset
          )
        );
      }
    }
    return effects;
  }

  private clearMarkHighlighting(
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
        effects.push(
          this.createClearHighlightEffect(
            highlightType,
            decorationKey,

          )
        );
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
      self.buildLineHighlighting(editor, chunkArray);
    let MarkHighlightEffects: StateEffect<unknown>[] =
      self.buildMarkHighlighting(editor, diffRanges, type);
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
    let clearLineHighlightEffects: StateEffect<unknown>[] =
      self.clearLineHighlighting(editor, chunkArray);
    let clearMarkHighlightEffects: StateEffect<unknown>[] =
      self.clearMarkHighlighting(editor, diffRanges, type);
    let effects: StateEffect<unknown>[] =
      clearLineHighlightEffects.concat(clearMarkHighlightEffects);
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
  dealigned: boolean;
  forceUpdate: Function;
  chunks: Chunk[];
  lineChunks: Chunk[];
  gap: HTMLElement;
  lockScroll: boolean;
  updating: boolean;
  updatingFast: boolean;
  collapsedRanges: { line: number; size: number }[] = [];

  protected updateCallback: (force?: boolean) => void;
  protected copyButtons: HTMLElement;
  protected lockButton: HTMLElement;
  //protected classes: DiffClasses | null;
}

// Updating the marks for editor content

/*function clearMergeMarks(editor: CodeMirror.Editor, arr: Marker[]) {
  for (let postfix of ['-local', '-remote', '-either', '-custom']) {
    let classes = copyObj(mergeClassPrefix);
    for (let k of Object.keys(classes)) {
      classes[k] += postfix;
    }
    clearMarks(editor, arr, classes);
  }
}*/


/*function isTextMarker(marker: Marker): marker is CodeMirror.TextMarker {
  return 'clear' in marker;
}*/

/*function clearMarks(editor: CodeMirror.Editor, arr: Marker[], classes: DiffClasses) {
  for (let i = arr.length - 1; i >= 0; --i) {
    let mark = arr[i];
    if (isTextMarker(mark)) {
      mark.clear();
      arr.splice(i, 1);
    } else if ((mark as any).parent) {
      editor.removeLineClass(mark, 'background', classes.chunk);
      editor.removeLineClass(mark, 'background', classes.start);
      editor.removeLineClass(mark, 'background', classes.end);
      editor.removeLineClass(mark, 'background', CHUNK_CONFLICT_CLASS);
      // Merge editor does not set a marker currently, so don't clear for it:
      if (valueIn(classes.gutter, [leftClasses.gutter, rightClasses.gutter])) {
        editor.setGutterMarker(mark, GUTTER_PICKER_CLASS, null);
      } else {
        editor.setGutterMarker(mark, GUTTER_CONFLICT_CLASS, null);
      }
      let line = editor.lineInfo(mark);
      if (!line.bgClass || line.bgClass.length === 0) {
        arr.splice(i, 1);
      }
    }
  }
}*/



/*function highlightChars(editor: CodeMirror.Editor, ranges: DiffRangePos[],
                        markers: Marker[], cls: string) {
  let doc = editor.getDoc();
  let origCls: string | null = null;
  if (valueIn(cls, [mergeClassPrefix.del, mergeClassPrefix.insert])) {
    origCls = cls;
  }
  for (let r of ranges) {
    if (origCls !== null) {
      cls = origCls + (r.source ? '-' + r.source.action : '');
    }
    markers.push(doc.markText(r.from, r.to, {className: cls}));
  }
}*/

// Updating the gap between editor and original

/**
 * From a line in base, find the matching line in another editor by chunks.
 */
/*function getMatchingEditLine(baseLine: number, chunks: Chunk[]): number {
  let offset = 0;
  // Start values correspond to either the start of the chunk,
  // or the start of a preceding unmodified part before the chunk.
  // It is the difference between these two that is interesting.
  for (let i = 0; i < chunks.length; i++) {
    let chunk = chunks[i];
    if (chunk.baseTo > baseLine && chunk.baseFrom <= baseLine) {
      return 0;
    }
    if (chunk.baseFrom > baseLine) {
      break;
    }
    offset = chunk.remoteTo - chunk.baseTo;
  }
  return baseLine + offset;
}*/

/**
 * From a line in base, find the matching line in another editor by line chunks
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
 *   algined line #2 ..., etc.]
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
      // Check agains existing matches to see if already consumed:
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
  return linesToAlign;
}

/*function alignLines(cm: CodeMirror.Editor[], lines: number[], aligners: CodeMirror.LineWidget[]): void {
  let maxOffset = 0;
  let offset: number[] = [];
  for (let i = 0; i < cm.length; i++) {
    if (lines[i] !== null) {
      let off = cm[i].heightAtLine(lines[i], 'local');
      offset[i] = off;
      maxOffset = Math.max(maxOffset, off);
    }
  }
  for (let i = 0; i < cm.length; i++) {
    if (lines[i] !== null) {
      let diff = maxOffset - offset[i];
      if (diff > 1) {
        aligners.push(padAbove(cm[i], lines[i], diff));
      }
    }
  }
}
*/

/* CM6 */
function alignLines(editors: EditorView[], lines: number[]): void {
  let maxPosFromTop = 0;
  let posFromTop: number[] = []; /*top position of the padding relative to the top of the document */
  let effects: StateEffect<unknown>[] = [];
  let editorNames: string[] = ['base', 'left','right', 'merge'];

  for (let i = 0; i < editors.length; i++) {
    if (lines[i] !== null) {
      let offset = editors[i].state.doc.line(lines[i]).from;
      console.log('offset:', offset);
      posFromTop[i] = editors[i].lineBlockAt(offset).top;
      maxPosFromTop = Math.max(maxPosFromTop, posFromTop[i]);
    };
  }
  for (let i = 0; i < editors.length; i++) {
    if (lines[i] !== null) {
      let height = maxPosFromTop - posFromTop[i];
      console.log('*******************************');
      console.log(editorNames[i]);
      console.log('posFromTop:', posFromTop);
      console.log('height', height);
      console.log('lines[i]:', lines[i]);
      if (height > 1) { /* height is in pixels*/
        effects.push(createPaddingEffect(editors[i], lines[i], height));
        editors[i].dispatch({ effects:effects });
      }
    }
  }
}

/* function padAbove(cm: CodeMirror.Editor, line: number, size: number): CodeMirror.LineWidget {
  let above = true;
  if (line > cm.getDoc().lastLine()) {
    line--;
    above = false;
  }
  let elt = document.createElement('div');
  elt.className = 'CodeMirror-merge-spacer';
  elt.style.height = size + 'px'; elt.style.minWidth = '1px';
  return cm.addLineWidget(line, elt, {height: size, above: above});
}
*/


/* Replaces the CM5 padAbove function */
function createPaddingEffect(editor: EditorView, line: number, size: number)  {
  let above = false;
  let offset: number = editor.state.doc.length;
  if (line <= editor.state.doc.lines) {
    above = true;
  }
  offset = editor.state.doc.line(line).from;
  console.log('In createPadding, offset is:', offset);
  console.log('In createPadding, line is:', line);
    const effect = addPaddingWidgetEffect.of({
      offset: offset,
      size: size,
      above: above
    });
  return effect;
}

export interface IMergeViewEditorConfiguration
  extends LegacyCodeMirror.EditorConfiguration {
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
    let remote = options.remote;
    let local = options.local || null;
    let merged = options.merged || null;
    //let panes: number = 0;
    let left: DiffView | null = (this.left = null);
    let right: DiffView | null = (this.right = null);
    let merge: DiffView | null = (this.merge = null);
    //let self = this;
    this.diffViews = [];
    /*this.aligners = [];*/
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

    this.gridPanel = new Panel();
    this.gridPanel.addClass('cm-grid-panel');
    this.addWidget(this.gridPanel);

    if (merged) {
      //options.gutters = [GUTTER_CONFLICT_CLASS, GUTTER_PICKER_CLASS];
      if (options.lineWrapping === undefined) {
        // Turn off linewrapping for merge view by default, keep for diff
        options.lineWrapping = false;
      }
    }

    //this.base = new EditorWidget(options.value, copyObj({readOnly: !!options.readOnly}, options));
    this.base = new EditorWidget(options.value);
    this.base.editor.injectExtension(getCommonEditorExtensions());

    if (merged) {
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
          this.alignViews.bind(this),
          copyObj(dvOptions)
        );
        this.diffViews.push(left);
        leftWidget = left.remoteEditorWidget;
      }
      this.gridPanel.addWidget(leftWidget);
      leftWidget.addClass('.cm-left-editor');
      //leftWidget.addClass('cm-mergeViewEditor');

      if (showBase) {
        this.gridPanel.addWidget(this.base);
        this.base.addClass('.cm-central-editor');
        //this.base.addClass('cm-mergeViewEditor');
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
          this.alignViews.bind(this),
          copyObj(dvOptions)
        );
        this.diffViews.push(right);
        rightWidget = right.remoteEditorWidget;
      }
      //rightWidget.addClass('cm-mergeViewEditor');
      this.gridPanel.addWidget(rightWidget);
      rightWidget.addClass('cm-right-editor');

      /*this.addWidget(new Widget({
        node: elt('div', null, 'CodeMirror-merge-clear', 'height: 0; clear: both;')
      }));*/

      merge = this.merge = new DiffView(
        merged,
        'merge',
        this.alignViews.bind(this),
        copyObj({ readOnly }, copyObj(dvOptions))
      );
      this.diffViews.push(merge);
      let mergeWidget = merge.remoteEditorWidget;
      // mergeWidget.addClass('cm-mergeViewEditor');
      this.gridPanel.addWidget(mergeWidget);
      mergeWidget.addClass('cm-merge-editor');
    } else if (remote) {
      // If in place for type guard

      this.gridPanel.addWidget(this.base);
      if (remote.unchanged || remote.added || remote.deleted) {
        if (remote.unchanged) {
          //this.base.addClass('CodeMirror-merge-pane-unchanged');
        } else if (remote.added) {
          //this.base.addClass('CodeMirror-merge-pane-added');
        } else if (remote.deleted) {
          //this.base.addClass('CodeMirror-merge-pane-deleted');
        }
      } else {
        right = this.right = new DiffView(
          remote,
          'right',
          this.alignViews.bind(this),
          dvOptions
        );
        this.diffViews.push(right);
        let rightWidget = right.remoteEditorWidget;

        //rightWidget.addClass('CodeMirror-merge-pane-remote');
        //this.addWidget(new Widget({node: right.buildGap()}));

        //rightWidget.addClass('cm-mergeViewEditor');
        this.gridPanel.addWidget(rightWidget);
        rightWidget.addClass('cm-right-editor');

        //panes = 2;
      }
      /*this.addWidget(new Widget({
        node: elt('div', null, 'CodeMirror-merge-clear', 'height: 0; clear: both;')
      }));*/
    }

    for (let dv of [left, right, merge]) {
      if (dv) {
        dv.init(this.base);
      }
    }

    /* if (options.collapseIdentical && panes > 1) {
      this.base.cm.operation(function() {
          collapseIdenticalStretches(self, options.collapseIdentical);
      });
    }
    */
    for (let dv of [left, right, merge]) {
      if (dv) {
        dv.collapsedRanges = this.collapsedRanges;
      }
    }
    this.initialized = true;
    if (this.left || this.right || this.merge) {
      this.alignViews(true);
    }
  }

  ////////////////////////////END OF CONSTRUCTOR//////////////////////////////////

  //alignViews(force?: boolean) {
    /* let dealigned = false;
    if (!this.initialized) {
      return;
    }
    for (let dv of this.diffViews) {
      dv.syncModel();
      if (dv.dealigned) {
        dealigned = true;
        dv.dealigned = false;
      }
    }

    if (!dealigned && !force) {
      return; // Nothing to do
    }
    // Find matching lines
    let linesToAlign = findAlignedLines(this.diffViews);

    // Function modifying DOM to perform alignment:
    let self: MergeView = this;
    let f = function () {

      // Clear old aligners
      let aligners = self.aligners;
      for (let i = 0; i < aligners.length; i++) {
        aligners[i].clear();
      }
      aligners.length = 0;

      // Editors (order is important, so it matches
      // format of linesToAlign)
      let cm: CodeMirror.Editor[] = [self.base.cm];
      let scroll: number[] = [];
      for (let dv of self.diffViews) {
        cm.push(dv.remoteEditor);
      }
      for (let i = 0; i < cm.length; i++) {
        scroll.push(cm[i].getScrollInfo().top);
      }

      for (let ln = 0; ln < linesToAlign.length; ln++) {
        alignLines(cm, linesToAlign[ln], aligners);
      }

      for (let i = 0; i < cm.length; i++) {
        cm[i].scrollTo(null, scroll[i]);
      }
    };

    // All editors should have an operation (simultaneously),
    // so set up nested operation calls.
    if (!this.base.cm.curOp) {
      f = function(fn) {
        return function() { self.base.cm.operation(fn); };
      }(f);
    }
    for (let dv of this.diffViews) {
      if (!dv.remoteEditor.curOp) {
        f = function(fn) {
          return function() { dv.remoteEditor.operation(fn); };
        }(f);
      }
    }
    // Perform alignment
    f();
  /*}


  /*CM6 version */
  alignViews(force?: boolean) {
    //console.log('Enter alighViews:');
     let dealigned = false;
    if (!this.initialized) {
      return;
    }
    for (let dv of this.diffViews) {
      dv.syncModel();
      if (dv.dealigned) {
        dealigned = true;
        dv.dealigned = false;
      }
    }

    if (!dealigned && !force) {
      return; // Nothing to do
    }
    // Find matching lines
    let linesToAlign = findAlignedLines(this.diffViews);
    //console.log('linesToAlign:', linesToAlign);

    // Function modifying DOM to perform alignment:
    let self: MergeView = this;
    /*let f = function () {*/

      // Clear old aligners
      //let aligners = self.aligners;
      /*for (let i = 0; i < aligners.length; i++) {
        /*aligners[i].clear();*/
        //console.log('implement a clear method for the aligners')
      //}
      //aligners.length = 0;

      /*// Editors (order is important, so it matches format of linesToAlign)
      let cm: CodeMirror.Editor[] = [self.base.cm];
      let scroll: number[] = [];
      for (let dv of self.diffViews) {
        cm.push(dv.remoteEditor);
      }*/

      let editors: EditorView[] = [self.base.cm];
      /*let scroll: number[] = [];*/
      for (let dv of self.diffViews) {
        editors.push(dv.remoteEditorWidget.cm);
      }
      for (let i = 0; i < editors.length; i++) {
        /*scroll.push(cm[i].getScrollInfo().top);*/
      }

      for (let ln = 0; ln < linesToAlign.length; ln++) {
        alignLines(editors, linesToAlign[ln]);
      }

      for (let i = 0; i < editors.length; i++) {
       /* editors[i].scrollTo(null, scroll[i]);*/
      }
    };



  setShowDifferences(val: boolean) {
    /* if (this.right) {
      this.right.setShowDifferences(val);
    }
    if (this.left) {
      this.left.setShowDifferences(val);
    } */
  }

  getMergedValue(): string {
    /*if (!this.merge) {
      throw new Error('No merged value; missing "merged" view');
    }
    return this.merge.remoteEditor.getValue();*/
    return '';
  }
  //splitPanel: SplitPanel;
  gridPanel: Panel;
  subPanel1: Panel;
  subPanel2: Panel;
  left: DiffView | null;
  right: DiffView | null;
  merge: DiffView | null;
  base: EditorWidget;
  options: any;
  diffViews: DiffView[];
  //aligners: PaddingWidget[];
  initialized: boolean = false;
  collapsedRanges: { size: number; line: number }[] = [];
}

/*function collapseSingle(cm: CodeMirror.Editor, from: number, to: number): {mark: CodeMirror.TextMarker, clear: () => void} {
  cm.addLineClass(from, 'wrap', 'CodeMirror-merge-collapsed-line');
  let widget = document.createElement('span');
  widget.className = 'CodeMirror-merge-collapsed-widget';
  widget.title = 'Identical text collapsed. Click to expand.';
  let mark = cm.getDoc().markText(
    CodeMirror.Pos(from, 0), CodeMirror.Pos(to - 1),
    {
      inclusiveLeft: true,
      inclusiveRight: true,
      replacedWith: widget,
      clearOnEnter: true
    }
  );
  function clear() {
    mark.clear();
    cm.removeLineClass(from, 'wrap', 'CodeMirror-merge-collapsed-line');
  }
  CodeMirror.on(widget, 'click', clear);
  return {mark: mark, clear: clear};
}*/

/*function collapseStretch(size: number, editors: {line: number, cm: CodeMirror.Editor}[]): CodeMirror.TextMarker {
  let marks: {mark: CodeMirror.TextMarker, clear: () => void}[] = [];
  function clear() {
    for (let i = 0; i < marks.length; i++) {
      marks[i].clear();
    }
  }
  for (let i = 0; i < editors.length; i++) {
    let editor = editors[i];
    let mark = collapseSingle(editor.cm, editor.line, editor.line + size);
    marks.push(mark);
    // Undocumented, but merge.js used it, so follow their lead:
    (mark.mark as any).on('clear', clear);
  }
  return marks[0].mark;
}*/

/*function unclearNearChunks(dv: DiffView, margin: number, off: number, clear: boolean[]): void {
  for (let i = 0; i < dv.chunks.length; i++) {
    let chunk = dv.chunks[i];
    for (let l = chunk.baseFrom - margin; l < chunk.baseTo + margin; l++) {
      let pos = l + off;
      if (pos >= 0 && pos < clear.length) {
        clear[pos] = false;
      }
    }
  }
}*/

/*function collapseIdenticalStretches(mv: MergeView, margin?: boolean | number): void {
  // FIXME: Use all panes
  if (typeof margin !== 'number') {
    margin = 2;
  }
  let clear: boolean[] = [];
  let edit = mv.base.cm;
  let off = edit.getDoc().firstLine();
  for (let l = off, e = edit.getDoc().lastLine(); l <= e; l++) {
    clear.push(true);
  }
  if (mv.left) {
    unclearNearChunks(mv.left, margin, off, clear);
  }
  if (mv.right) {
    unclearNearChunks(mv.right, margin, off, clear);
  }
  if (mv.merge) {
    unclearNearChunks(mv.merge, margin, off, clear);
  }
  mv.collapsedRanges = [];
  for (let i = 0; i < clear.length; i++) {
    if (clear[i]) {
      let line = i + off;
      let size = 1;
      for (; i < clear.length - 1 && clear[i + 1]; i++, size++) {
        // Just finding size
      }
      if (size > margin) {
        let editors: {line: number, cm: CodeMirror.Editor}[] =
          [{line: line, cm: edit}];
        if (mv.left) {
          editors.push({line: getMatchingEditLine(line, mv.left.chunks),
            cm: mv.left.remoteEditor});
        }
        if (mv.right) {
          editors.push({line: getMatchingEditLine(line, mv.right.chunks),
            cm: mv.right.remoteEditor});
        }
        if (mv.merge) {
          editors.push({line: getMatchingEditLine(line, mv.merge.chunks),
            cm: mv.merge.remoteEditor});
        }
        let mark = collapseStretch(size, editors);
        mv.collapsedRanges.push({line, size});
        (mark as any).on('clear', () => {
          for (let i=0; i < mv.collapsedRanges.length; ++i) {
            let range = mv.collapsedRanges[i];
            if (range.line === line) {
              mv.collapsedRanges.splice(i, 1);
              return;
            }
          }
        });
        if (mv.options.onCollapse) {
          mv.options.onCollapse(mv, line, size, mark);
        }
      }
    }
  }
}*/

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

/*function findPrevDiff(chunks: Chunk[], start: number, isOrig: boolean): number | null {
  for (let i = chunks.length - 1; i >= 0; i--) {
    let chunk = chunks[i];
    let to = (isOrig ? chunk.remoteTo : chunk.baseTo) - 1;
    if (to < start) {
      return to;
    }
  }
  return null;
}*/

/*function findNextDiff(chunks: Chunk[], start: number, isOrig: boolean): number | null {
  for (let i = 0; i < chunks.length; i++) {
    let chunk = chunks[i];
    let from = (isOrig ? chunk.remoteFrom : chunk.baseFrom);
    if (from > start) {
      return from;
    }
  }
  return null;
}*/

/*enum DiffDirection {
  Previous = -1,
  Next = 1
}*/

/*function goNearbyDiff(cm: CodeMirror.Editor, dir: DiffDirection): void | any {
  let found: number | null = null;
  let views = cm.state.diffViews as DiffView[];
  let line = cm.getDoc().getCursor().line;
  if (views) {
    for (let i = 0; i < views.length; i++) {
      let dv = views[i];
      let isOrig = cm === dv.remoteEditor;
      let pos = dir === DiffDirection.Previous ?
        findPrevDiff(dv.chunks, line, isOrig) :
        findNextDiff(dv.chunks, line, isOrig);
      if (pos !== null && (found === null ||
            (dir === DiffDirection.Previous ? pos > found : pos < found))) {
        found = pos;
      }
    }
  }
  if (found !== null) {
    cm.getDoc().setCursor(found, 0);
  } else {
    return CodeMirror.Pass;
  }
}*/

/*CodeMirror.commands.goNextDiff = function(cm: CodeMirror.Editor) {
  return goNearbyDiff(cm, DiffDirection.Next);
};
CodeMirror.commands.goPrevDiff = function(cm: CodeMirror.Editor) {
  return goNearbyDiff(cm, DiffDirection.Previous);
};
*/
