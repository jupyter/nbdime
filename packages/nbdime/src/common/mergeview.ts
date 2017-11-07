// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.

// This code is based on the CodeMirror mergeview.js source:
// CodeMirror, copyright (c) by Marijn Haverbeke and others
// Distributed under an MIT license: http://codemirror.net/LICENSE

'use strict';

import * as CodeMirror from 'codemirror';

import {
  Widget, Panel
} from '@phosphor/widgets';

import {
  Mode
} from '@jupyterlab/codemirror';

import {
  IStringDiffModel
} from '../diff/model';

import {
  DecisionStringDiffModel
} from '../merge/model';

import {
  DiffRangePos
} from '../diff/range';

import {
  ChunkSource, Chunk, lineToNormalChunks
} from '../chunking';

import {
  EditorWidget
} from './editor';

import {
  valueIn, hasEntries, splitLines, copyObj
} from './util';

import {
  NotifyUserError
} from './exceptions';


const PICKER_SYMBOL = '\u27ad';

const CONFLICT_MARKER = '\u26A0'; // '\u2757'


export
type Marker = CodeMirror.LineHandle | CodeMirror.TextMarker;

export
enum DIFF_OP {
  DIFF_DELETE = -1,
  DIFF_INSERT = 1,
  DIFF_EQUAL = 0
}

export
enum EventDirection {
  INCOMING,
  OUTGOING
}

export
type DiffClasses = {
  [key: string]: string;
  chunk: string,
  start: string,
  end: string,
  insert: string,
  del: string,
  connect: string,
  gutter: string
};


const GUTTER_PICKER_CLASS = 'jp-Merge-gutter-picker';
const GUTTER_CONFLICT_CLASS = 'jp-Merge-gutter-conflict';

const CHUNK_CONFLICT_CLASS = 'jp-Merge-conflict';

const leftClasses: DiffClasses = { chunk: 'CodeMirror-merge-l-chunk',
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

const mergeClassPrefix: DiffClasses = {chunk: 'CodeMirror-merge-m-chunk',
          start: 'CodeMirror-merge-m-chunk-start',
          end: 'CodeMirror-merge-m-chunk-end',
          insert: 'CodeMirror-merge-m-inserted',
          del: 'CodeMirror-merge-m-deleted',
          connect: 'CodeMirror-merge-m-connect',
          gutter: 'CodeMirror-merge-m-gutter'};


/**
 * A wrapper view for showing StringDiffModels in a MergeView
 */
export function createNbdimeMergeView(remote: IStringDiffModel): MergeView;
export function createNbdimeMergeView(
      remote: IStringDiffModel | null,
      local: IStringDiffModel | null,
      merged: IStringDiffModel,
      readOnly?: boolean): MergeView;
export
function createNbdimeMergeView(
      remote: IStringDiffModel | null,
      local?: IStringDiffModel | null,
      merged?: IStringDiffModel,
      readOnly?: boolean): MergeView {
  let opts: IMergeViewEditorConfiguration = {
    remote,
    local,
    merged,
    readOnly,
    orig: null};
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
      e.ownWidget.model.mimeType = mimetype;
    }
    mergeview.base.model.mimeType = mimetype;
  }
  return mergeview;
}


/**
 * Used by MergeView to show diff in a string diff model
 */
export
class DiffView {
  constructor(model: IStringDiffModel,
              type: 'left' | 'right' | 'merge',
              updateCallback: (force?: boolean) => void,
              options: CodeMirror.MergeView.MergeViewEditorConfiguration) {
    this.model = model;
    this.type = type;
    this.updateCallback = updateCallback;
    this.classes = type === 'left' ?
      leftClasses : type === 'right' ? rightClasses : null;
    let ownValue = this.model.remote || '';
    this.ownWidget = new EditorWidget(ownValue, copyObj({readOnly: !!options.readOnly}, options));
    this.showDifferences = options.showDifferences !== false;
  }

  init(base: CodeMirror.Editor) {
    this.baseEditor = base;
    (this.baseEditor.state.diffViews ||
     (this.baseEditor.state.diffViews = [])).push(this);
    this.ownEditor.state.diffViews = [this];

    this.baseEditor.on('gutterClick', this.onGutterClick.bind(this));
    this.ownEditor.on('gutterClick', this.onGutterClick.bind(this));

    this.lineChunks = this.model.getLineChunks();
    this.chunks = lineToNormalChunks(this.lineChunks);
    this.dealigned = false;

    this.forceUpdate = this.registerUpdate();
    this.setScrollLock(true, false);
    this.registerScroll();
  }

  setShowDifferences(val: boolean) {
    val = val !== false;
    if (val !== this.showDifferences) {
      this.showDifferences = val;
      this.forceUpdate('full');
    }
  }

  syncModel() {
    if (this.modelInvalid()) {
      let edit = this.ownEditor;
      let cursor = edit.getDoc().getCursor();
      let newLines = splitLines(this.model.remote!);
      let start = edit.getDoc().firstLine();
      let last = edit.getDoc().lastLine();
      let end = last;
      for (let range of this.collapsedRanges) {
        let baseLine = range.line;
        end = getMatchingEditLine(baseLine, this.chunks);
        if (end !== start) {
          edit.getDoc().replaceRange(newLines.slice(start, end - 1).join(''), CodeMirror.Pos(start, 0), CodeMirror.Pos(end - 1, 0));
        }
        start = end + range.size;
      }
      if (start < last) {
        edit.getDoc().replaceRange(newLines.slice(start, end).join(''), CodeMirror.Pos(start, 0), CodeMirror.Pos(end, 0));
      }
      this.ownEditor.getDoc().setCursor(cursor);
      this.lineChunks = this.model.getLineChunks();
      this.chunks = lineToNormalChunks(this.lineChunks);
    }
  }

  buildGap(): HTMLElement {
    let lock = this.lockButton = elt('div', undefined, 'CodeMirror-merge-scrolllock');
    lock.title = 'Toggle locked scrolling';
    let lockWrap = elt('div', [lock], 'CodeMirror-merge-scrolllock-wrap');
    let self: DiffView = this;
    CodeMirror.on(lock, 'click', function() {
      self.setScrollLock(!self.lockScroll);
    });
    return this.gap = elt('div', [lockWrap], 'CodeMirror-merge-gap');
  }

  setScrollLock(val: boolean, action?: boolean) {
    this.lockScroll = val;
    if (val && action !== false) {
      this.syncScroll(EventDirection.OUTGOING);
    }
    if (this.lockButton) {
      this.lockButton.innerHTML = val ? '\u21db\u21da' : '\u21db&nbsp;&nbsp;\u21da';
    }
  }

  protected registerUpdate() {
    let editMarkers: Marker[] = [];
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
          clearMergeMarks(self.baseEditor, editMarkers);
          clearMergeMarks(self.ownEditor, origMarkers);
        } else {
          clearMarks(self.baseEditor, editMarkers, self.classes);
          clearMarks(self.ownEditor, origMarkers, self.classes);
        }
      }
      if (self.showDifferences) {
        self.updateMarks(
          self.ownEditor, self.model.additions,
          editMarkers, DIFF_OP.DIFF_INSERT);
        self.updateMarks(
          self.baseEditor, self.model.deletions,
          origMarkers, DIFF_OP.DIFF_DELETE);
      }

      self.updateCallback(true);
      checkSync(self.ownEditor);
      self.updating = false;
    }
    function setDealign(fast: boolean | CodeMirror.Editor) {
        let upd = false;
        for (let dv of self.baseEditor.state.diffViews) {
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
      for (let dv of self.baseEditor.state.diffViews) {
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
    function change(_cm: CodeMirror.Editor, change: CodeMirror.EditorChangeLinkedList) {
      if (self.model instanceof DecisionStringDiffModel) {
        self.model.invalidate();
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
    this.baseEditor.on('change', change);
    this.ownEditor.on('change', change);
    this.baseEditor.on('markerAdded', setDealign);
    this.baseEditor.on('markerCleared', setDealign);
    this.ownEditor.on('markerAdded', setDealign);
    this.ownEditor.on('markerCleared', setDealign);
    this.baseEditor.on('viewportChange', function() { set(false); });
    this.ownEditor.on('viewportChange', function() { set(false); });
    update();
    return update;
  }

  protected modelInvalid(): boolean {
    return this.model instanceof DecisionStringDiffModel &&
            this.model.invalid;
  }

  protected onGutterClick(instance: CodeMirror.Editor, line: number, gutter: string, clickEvent: MouseEvent): void {
    if (clickEvent.button !== 0) {
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
        if (instance === this.ownEditor) {
          for (let s of ss) {
            s.decision.action = s.action;
          }
        } else if (instance === this.baseEditor) {
          for (let s of ss) {
            s.decision.action = 'base';
            if (hasEntries(s.decision.customDiff)) {
              s.decision.customDiff = [];
            }
          }
        }
      } else if (gutter === GUTTER_CONFLICT_CLASS) {
        for (let s of ss) {
          s.decision.conflict = false;
        }
      }
      for (let dv of this.baseEditor.state.diffViews as DiffView[]) {
        if (dv.model instanceof DecisionStringDiffModel) {
          dv.model.invalidate();
        }
        dv.forceUpdate('full');
      }
    }
  }

  protected registerScroll(): void {
    let self = this;
    this.baseEditor.on('scroll', function() {
      self.syncScroll(EventDirection.OUTGOING);
    });
    this.ownEditor.on('scroll', function() {
      self.syncScroll(EventDirection.INCOMING);
    });
  }

  /**
   * Sync scrolling between base and own editors. `type` is used to indicate
   * which editor is the source, and which editor is the destination of the sync.
   */
  protected syncScroll(type: EventDirection): void {
    if (this.modelInvalid()) {
      return;
    }
    if (!this.lockScroll) {
      return;
    }
    // editor: What triggered event, other: What needs to be synced
    let editor: CodeMirror.Editor;
    let other: CodeMirror.Editor;
    if (type === EventDirection.OUTGOING) {
      editor = this.baseEditor;
      other = this.ownEditor;
    } else {
      editor = this.ownEditor;
      other = this.baseEditor;
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
    return;
  }


  protected updateMarks(editor: CodeMirror.Editor, diff: DiffRangePos[],
                        markers: Marker[], type: DIFF_OP) {
    let classes: DiffClasses;
    if (this.classes === null) {
      // Only store prefixes here, will be completed later
      classes = copyObj(mergeClassPrefix);
    } else {
      classes = this.classes;
    }

    let self = this;
    function markChunk(editor: CodeMirror.Editor, from: number, to: number,
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
          } else if (conflict && editor === self.ownEditor) {
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
      let edit = editor === self.baseEditor;
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
  }

  get ownEditor(): CodeMirror.Editor {
    return this.ownWidget.cm;
  }

  ownWidget: EditorWidget;
  model: IStringDiffModel;
  type: string;
  showDifferences: boolean;
  dealigned: boolean;
  forceUpdate: Function;
  baseEditor: CodeMirror.Editor;
  chunks: Chunk[];
  lineChunks: Chunk[];
  gap: HTMLElement;
  lockScroll: boolean;
  updating: boolean;
  updatingFast: boolean;
  collapsedRanges: {line: number, size: number}[] = [];

  protected updateCallback: (force?: boolean) => void;
  protected copyButtons: HTMLElement;
  protected lockButton: HTMLElement;
  protected classes: DiffClasses | null;
}


// Updating the marks for editor content

function clearMergeMarks(editor: CodeMirror.Editor, arr: Marker[]) {
  for (let postfix of ['-local', '-remote', '-either', '-custom']) {
    let classes = copyObj(mergeClassPrefix);
    for (let k of Object.keys(classes)) {
      classes[k] += postfix;
    }
    clearMarks(editor, arr, classes);
  }
}

function isTextMarker(marker: Marker): marker is CodeMirror.TextMarker {
  return 'clear' in marker;
}

function clearMarks(editor: CodeMirror.Editor, arr: Marker[], classes: DiffClasses) {
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
}

function highlightChars(editor: CodeMirror.Editor, ranges: DiffRangePos[],
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
}


// Updating the gap between editor and original


/**
 * From a line in base, find the matching line in another editor by chunks.
 */
function getMatchingEditLine(baseLine: number, chunks: Chunk[]): number {
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
}


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
 * Find which line numbers align which each other, in the
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


function alignLines(cm: CodeMirror.Editor[], lines: number[], aligners: CodeMirror.LineWidget[]): void {
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

function padAbove(cm: CodeMirror.Editor, line: number, size: number): CodeMirror.LineWidget {
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


export
interface IMergeViewEditorConfiguration extends CodeMirror.EditorConfiguration {
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
export
class MergeView extends Panel {
  constructor(options: IMergeViewEditorConfiguration) {
    super();
    this.options = options;
    let remote = options.remote;
    let local = options.local || null;
    let merged = options.merged || null;

    let panes: number = 0;
    let left: DiffView | null = this.left = null;
    let right: DiffView | null = this.right = null;
    let merge: DiffView | null = this.merge = null;
    let self = this;
    this.diffViews = [];
    this.aligners = [];
    let main = options.remote || options.merged;
    if (!main) {
      throw new Error('Either remote or merged model needs to be specified!');
    }
    options.value = (main.base !== null ?
      main.base : main.remote);
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

    let dvOptions = options as CodeMirror.MergeView.MergeViewEditorConfiguration;

    if (merged) {
      options.gutters = [GUTTER_CONFLICT_CLASS, GUTTER_PICKER_CLASS];
      if (options.lineWrapping === undefined) {
        // Turn off linewrapping for merge view by default, keep for diff
        options.lineWrapping = false;
      }
    }

    this.base = new EditorWidget(options.value, copyObj({readOnly: !!options.readOnly}, options));
    this.base.addClass('CodeMirror-merge-pane');
    this.base.addClass('CodeMirror-merge-pane-base');

    if (merged) {
      let showBase = options.showBase !== false;
      if (!showBase) {
        this.base.node.style.display = 'hidden';
      }

      let leftWidget: Widget;
      if (!local || local.remote === null) {
        // Local value was deleted
        left = this.left = null;
        leftWidget = new Widget({node: elt('div', 'Value missing', 'jp-mod-missing')});
      } else {
        left = this.left = new DiffView(local, 'left', this.alignViews.bind(this),
          copyObj(dvOptions));
        this.diffViews.push(left);
        leftWidget = left.ownWidget;
      }
      leftWidget.addClass('CodeMirror-merge-pane');
      leftWidget.addClass('CodeMirror-merge-pane-local');
      this.addWidget(leftWidget);

      if (showBase) {
        this.addWidget(this.base);
      }

      let rightWidget: Widget;
      if (!remote || remote.remote === null) {
        // Remote value was deleted
        right = this.right = null;
        rightWidget = new Widget({node: elt('div', 'Value missing', 'jp-mod-missing')});
      } else {
        right = this.right = new DiffView(remote, 'right', this.alignViews.bind(this),
          copyObj(dvOptions));
        this.diffViews.push(right);
        rightWidget = right.ownWidget;
      }
      rightWidget.addClass('CodeMirror-merge-pane');
      rightWidget.addClass('CodeMirror-merge-pane-remote');
      this.addWidget(rightWidget);

      this.addWidget(new Widget({
        node: elt('div', null, 'CodeMirror-merge-clear', 'height: 0; clear: both;')
      }));

      merge = this.merge = new DiffView(merged, 'merge', this.alignViews.bind(this),
        copyObj({readOnly}, copyObj(dvOptions)));
      this.diffViews.push(merge);
      let mergeWidget = merge.ownWidget;
      mergeWidget.addClass('CodeMirror-merge-pane');
      mergeWidget.addClass('CodeMirror-merge-pane-final');
      this.addWidget(mergeWidget);

      panes = 3 + (showBase ? 1 : 0);
    } else if (remote) { // If in place for type guard
      this.addWidget(this.base);
      if (remote.unchanged || remote.added || remote.deleted) {
        if (remote.unchanged) {
          this.base.addClass('CodeMirror-merge-pane-unchanged');
        } else if (remote.added) {
          this.base.addClass('CodeMirror-merge-pane-added');
        } else if (remote.deleted) {
          this.base.addClass('CodeMirror-merge-pane-deleted');
        }
        panes = 1;
      } else {
        right = this.right = new DiffView(remote, 'right', this.alignViews.bind(this), dvOptions);
        this.diffViews.push(right);
        let rightWidget = right.ownWidget;
        rightWidget.addClass('CodeMirror-merge-pane');
        rightWidget.addClass('CodeMirror-merge-pane-remote');
        this.addWidget(new Widget({node: right.buildGap()}));
        this.addWidget(rightWidget);
        panes = 2;
      }
      this.addWidget(new Widget({
        node: elt('div', null, 'CodeMirror-merge-clear', 'height: 0; clear: both;')
      }));
    }

    this.addClass('CodeMirror-merge');
    this.addClass('CodeMirror-merge-' + panes + 'pane');

    for (let dv of [left, right, merge]) {
      if (dv) {
        dv.init(this.base.cm);
      }
    }

    if (options.collapseIdentical && panes > 1) {
      this.base.cm.operation(function() {
          collapseIdenticalStretches(self, options.collapseIdentical);
      });
    }
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

  alignViews(force?: boolean) {
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
        cm.push(dv.ownEditor);
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
      if (!dv.ownEditor.curOp) {
        f = function(fn) {
          return function() { dv.ownEditor.operation(fn); };
        }(f);
      }
    }
    // Perform alignment
    f();
  }

  setShowDifferences(val: boolean) {
    if (this.right) {
      this.right.setShowDifferences(val);
    }
    if (this.left) {
      this.left.setShowDifferences(val);
    }
  }

  getMergedValue(): string {
    if (!this.merge) {
      throw new Error('No merged value; missing "merged" view');
    }
    return this.merge.ownEditor.getValue();
  }

  left: DiffView | null;
  right: DiffView | null;
  merge: DiffView | null;
  base: EditorWidget;
  options: any;
  diffViews: DiffView[];
  aligners: CodeMirror.LineWidget[];
  initialized: boolean = false;
  collapsedRanges: {size: number, line: number}[] = [];
}

function collapseSingle(cm: CodeMirror.Editor, from: number, to: number): {mark: CodeMirror.TextMarker, clear: () => void} {
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
}

function collapseStretch(size: number, editors: {line: number, cm: CodeMirror.Editor}[]): CodeMirror.TextMarker {
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
}

function unclearNearChunks(dv: DiffView, margin: number, off: number, clear: boolean[]): void {
  for (let i = 0; i < dv.chunks.length; i++) {
    let chunk = dv.chunks[i];
    for (let l = chunk.baseFrom - margin; l < chunk.baseTo + margin; l++) {
      let pos = l + off;
      if (pos >= 0 && pos < clear.length) {
        clear[pos] = false;
      }
    }
  }
}

function collapseIdenticalStretches(mv: MergeView, margin?: boolean | number): void {
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
            cm: mv.left.ownEditor});
        }
        if (mv.right) {
          editors.push({line: getMatchingEditLine(line, mv.right.chunks),
            cm: mv.right.ownEditor});
        }
        if (mv.merge) {
          editors.push({line: getMatchingEditLine(line, mv.merge.chunks),
            cm: mv.merge.ownEditor});
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
}

// General utilities

function elt(tag: string, content?: string | HTMLElement[] | null, className?: string | null, style?: string | null): HTMLElement {
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
      e.appendChild((content)[i]);
    }
  }
  return e;
}

function findPrevDiff(chunks: Chunk[], start: number, isOrig: boolean): number | null {
  for (let i = chunks.length - 1; i >= 0; i--) {
    let chunk = chunks[i];
    let to = (isOrig ? chunk.remoteTo : chunk.baseTo) - 1;
    if (to < start) {
      return to;
    }
  }
  return null;
}

function findNextDiff(chunks: Chunk[], start: number, isOrig: boolean): number | null {
  for (let i = 0; i < chunks.length; i++) {
    let chunk = chunks[i];
    let from = (isOrig ? chunk.remoteFrom : chunk.baseFrom);
    if (from > start) {
      return from;
    }
  }
  return null;
}

enum DiffDirection {
  Previous = -1,
  Next = 1
}

function goNearbyDiff(cm: CodeMirror.Editor, dir: DiffDirection): void | any {
  let found: number | null = null;
  let views = cm.state.diffViews as DiffView[];
  let line = cm.getDoc().getCursor().line;
  if (views) {
    for (let i = 0; i < views.length; i++) {
      let dv = views[i];
      let isOrig = cm === dv.ownEditor;
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
}

CodeMirror.commands.goNextDiff = function(cm: CodeMirror.Editor) {
  return goNearbyDiff(cm, DiffDirection.Next);
};
CodeMirror.commands.goPrevDiff = function(cm: CodeMirror.Editor) {
  return goNearbyDiff(cm, DiffDirection.Previous);
};
