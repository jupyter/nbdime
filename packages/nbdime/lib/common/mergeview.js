// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
// This code is based on the CodeMirror mergeview.js source:
// CodeMirror, copyright (c) by Marijn Haverbeke and others
// Distributed under an MIT license: http://codemirror.net/LICENSE
'use strict';
Object.defineProperty(exports, "__esModule", { value: true });
exports.MergeView = exports.DiffView = exports.createNbdimeMergeView = exports.EventDirection = exports.DIFF_OP = void 0;
const CodeMirror = require("codemirror");
const widgets_1 = require("@lumino/widgets");
const model_1 = require("../merge/model");
const chunking_1 = require("../chunking");
const editor_1 = require("./editor");
const util_1 = require("./util");
const exceptions_1 = require("./exceptions");
const PICKER_SYMBOL = '\u27ad';
const CONFLICT_MARKER = '\u26A0'; // '\u2757'
var DIFF_OP;
(function (DIFF_OP) {
    DIFF_OP[DIFF_OP["DIFF_DELETE"] = -1] = "DIFF_DELETE";
    DIFF_OP[DIFF_OP["DIFF_INSERT"] = 1] = "DIFF_INSERT";
    DIFF_OP[DIFF_OP["DIFF_EQUAL"] = 0] = "DIFF_EQUAL";
})(DIFF_OP = exports.DIFF_OP || (exports.DIFF_OP = {}));
var EventDirection;
(function (EventDirection) {
    EventDirection[EventDirection["INCOMING"] = 0] = "INCOMING";
    EventDirection[EventDirection["OUTGOING"] = 1] = "OUTGOING";
})(EventDirection = exports.EventDirection || (exports.EventDirection = {}));
const GUTTER_PICKER_CLASS = 'jp-Merge-gutter-picker';
const GUTTER_CONFLICT_CLASS = 'jp-Merge-gutter-conflict';
const CHUNK_CONFLICT_CLASS = 'jp-Merge-conflict';
const leftClasses = { chunk: 'CodeMirror-merge-l-chunk',
    start: 'CodeMirror-merge-l-chunk-start',
    end: 'CodeMirror-merge-l-chunk-end',
    insert: 'CodeMirror-merge-l-inserted',
    del: 'CodeMirror-merge-l-deleted',
    connect: 'CodeMirror-merge-l-connect',
    gutter: 'CodeMirror-merge-l-gutter' };
const rightClasses = { chunk: 'CodeMirror-merge-r-chunk',
    start: 'CodeMirror-merge-r-chunk-start',
    end: 'CodeMirror-merge-r-chunk-end',
    insert: 'CodeMirror-merge-r-inserted',
    del: 'CodeMirror-merge-r-deleted',
    connect: 'CodeMirror-merge-r-connect',
    gutter: 'CodeMirror-merge-r-gutter' };
const mergeClassPrefix = { chunk: 'CodeMirror-merge-m-chunk',
    start: 'CodeMirror-merge-m-chunk-start',
    end: 'CodeMirror-merge-m-chunk-end',
    insert: 'CodeMirror-merge-m-inserted',
    del: 'CodeMirror-merge-m-deleted',
    connect: 'CodeMirror-merge-m-connect',
    gutter: 'CodeMirror-merge-m-gutter' };
function createNbdimeMergeView(remote, local, merged, readOnly) {
    let opts = {
        remote,
        local,
        merged,
        readOnly,
        orig: null
    };
    opts.collapseIdentical = true;
    let mergeview = new MergeView(opts);
    let editors = [];
    if (mergeview.left) {
        editors.push(mergeview.left);
    }
    if (mergeview.right) {
        editors.push(mergeview.right);
    }
    if (mergeview.merge) {
        editors.push(mergeview.merge);
    }
    let mimetype = (remote || merged).mimetype;
    if (mimetype) {
        // Set the editor mode to the MIME type.
        for (let e of editors) {
            e.ownWidget.model.mimeType = mimetype;
        }
        mergeview.base.model.mimeType = mimetype;
    }
    return mergeview;
}
exports.createNbdimeMergeView = createNbdimeMergeView;
/**
 * Used by MergeView to show diff in a string diff model
 */
class DiffView {
    constructor(model, type, updateCallback, options) {
        this.collapsedRanges = [];
        this.model = model;
        this.type = type;
        this.updateCallback = updateCallback;
        this.classes = type === 'left' ?
            leftClasses : type === 'right' ? rightClasses : null;
        let ownValue = this.model.remote || '';
        this.ownWidget = new editor_1.EditorWidget(ownValue, util_1.copyObj({ readOnly: !!options.readOnly }, options));
        this.showDifferences = options.showDifferences !== false;
    }
    init(base) {
        this.baseEditor = base;
        (this.baseEditor.state.diffViews ||
            (this.baseEditor.state.diffViews = [])).push(this);
        this.ownEditor.state.diffViews = [this];
        this.baseEditor.on('gutterClick', this.onGutterClick.bind(this));
        this.ownEditor.on('gutterClick', this.onGutterClick.bind(this));
        this.lineChunks = this.model.getLineChunks();
        this.chunks = chunking_1.lineToNormalChunks(this.lineChunks);
        this.dealigned = false;
        this.forceUpdate = this.registerUpdate();
        this.setScrollLock(true, false);
        this.registerScroll();
    }
    setShowDifferences(val) {
        val = val !== false;
        if (val !== this.showDifferences) {
            this.showDifferences = val;
            this.forceUpdate('full');
        }
    }
    syncModel() {
        if (this.modelInvalid()) {
            let edit = this.ownEditor;
            let updatedLineChunks = this.model.getLineChunks();
            let updatedChunks = chunking_1.lineToNormalChunks(updatedLineChunks);
            if (this.model.remote === edit.getValue()) {
                // Nothing to do except update chunks
                this.lineChunks = updatedLineChunks;
                this.chunks = updatedChunks;
                return;
            }
            let cursor = edit.getDoc().getCursor();
            let newLines = util_1.splitLines(this.model.remote);
            let start = edit.getDoc().firstLine();
            let last = edit.getDoc().lastLine() + 1;
            let cumulativeOffset = 0;
            let end;
            let updatedEnd;
            // We want to replace contents of editor, but if we have collapsed regions
            // some lines have been optimized away. Carefully replace the relevant bits:
            for (let range of this.collapsedRanges) {
                let baseLine = range.line;
                end = getMatchingEditLine(baseLine, this.chunks);
                updatedEnd = getMatchingEditLine(baseLine, updatedChunks);
                let offset = updatedEnd - end;
                if (end !== start || offset !== 0) {
                    edit.getDoc().replaceRange(newLines.slice(start + cumulativeOffset, updatedEnd + cumulativeOffset - 1).join(''), CodeMirror.Pos(start, 0), CodeMirror.Pos(end - 1, 0), 'syncModel');
                }
                cumulativeOffset += offset;
                start = end + range.size;
            }
            if (start < last) {
                // Only here if no collapsed ranges, replace full contents
                edit.getDoc().replaceRange(newLines.slice(start, newLines.length).join(''), CodeMirror.Pos(start, 0), CodeMirror.Pos(last, 0), 'syncModel');
            }
            this.ownEditor.getDoc().setCursor(cursor);
            this.lineChunks = updatedLineChunks;
            this.chunks = updatedChunks;
        }
    }
    buildGap() {
        let lock = this.lockButton = elt('div', undefined, 'CodeMirror-merge-scrolllock');
        lock.title = 'Toggle locked scrolling';
        let lockWrap = elt('div', [lock], 'CodeMirror-merge-scrolllock-wrap');
        let self = this;
        CodeMirror.on(lock, 'click', function () {
            self.setScrollLock(!self.lockScroll);
        });
        return this.gap = elt('div', [lockWrap], 'CodeMirror-merge-gap');
    }
    setScrollLock(val, action) {
        this.lockScroll = val;
        if (val && action !== false) {
            this.syncScroll(EventDirection.OUTGOING);
        }
        if (this.lockButton) {
            this.lockButton.innerHTML = val ? '\u21db\u21da' : '\u21db&nbsp;&nbsp;\u21da';
        }
    }
    registerUpdate() {
        let editMarkers = [];
        let origMarkers = [];
        let debounceChange;
        let self = this;
        self.updating = false;
        self.updatingFast = false;
        function update(mode) {
            self.updating = true;
            self.updatingFast = false;
            if (mode === 'full') {
                self.syncModel();
                if (self.classes === null) {
                    clearMergeMarks(self.baseEditor, editMarkers);
                    clearMergeMarks(self.ownEditor, origMarkers);
                }
                else {
                    clearMarks(self.baseEditor, editMarkers, self.classes);
                    clearMarks(self.ownEditor, origMarkers, self.classes);
                }
            }
            if (self.showDifferences) {
                self.updateMarks(self.ownEditor, self.model.additions, editMarkers, DIFF_OP.DIFF_INSERT);
                self.updateMarks(self.baseEditor, self.model.deletions, origMarkers, DIFF_OP.DIFF_DELETE);
            }
            self.updateCallback(true);
            checkSync(self.ownEditor);
            self.updating = false;
        }
        function setDealign(fast) {
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
        function set(fast) {
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
        function change(_cm, change) {
            if (!(self.model instanceof model_1.DecisionStringDiffModel)) {
                // TODO: Throttle?
                self.lineChunks = self.model.getLineChunks();
                self.chunks = chunking_1.lineToNormalChunks(self.lineChunks);
            }
            // Update faster when a line was added/removed
            setDealign(change.text.length - 1 !== change.to.line - change.from.line);
        }
        function checkSync(cm) {
            if (self.model.remote !== cm.getValue()) {
                throw new exceptions_1.NotifyUserError('CRITICAL: Merge editor out of sync with model! ' +
                    'Double-check any saved merge output!');
            }
        }
        this.baseEditor.on('change', change);
        this.ownEditor.on('change', change);
        this.baseEditor.on('markerAdded', setDealign);
        this.baseEditor.on('markerCleared', setDealign);
        this.ownEditor.on('markerAdded', setDealign);
        this.ownEditor.on('markerCleared', setDealign);
        this.baseEditor.on('viewportChange', function () { set(false); });
        this.ownEditor.on('viewportChange', function () { set(false); });
        update();
        return update;
    }
    modelInvalid() {
        return this.model instanceof model_1.DecisionStringDiffModel &&
            this.model.invalid;
    }
    onGutterClick(instance, line, gutter, clickEvent) {
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
            let ss = node.sources;
            if (gutter === GUTTER_PICKER_CLASS) {
                if (instance === this.ownEditor) {
                    for (let s of ss) {
                        s.decision.action = s.action;
                    }
                }
                else if (this.type === 'merge' && instance === this.baseEditor) {
                    for (let s of ss) {
                        s.decision.action = 'base';
                    }
                }
                for (let i = ss.length - 1; i >= 0; --i) {
                    let s = ss[i];
                    if (this.type === 'merge' && util_1.hasEntries(s.decision.customDiff)) {
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
            }
            else if (gutter === GUTTER_CONFLICT_CLASS) {
                for (let s of ss) {
                    s.decision.conflict = false;
                }
            }
            for (let dv of this.baseEditor.state.diffViews) {
                if (dv.model instanceof model_1.DecisionStringDiffModel) {
                    dv.model.invalidate();
                }
                dv.forceUpdate('full');
            }
        }
    }
    registerScroll() {
        let self = this;
        this.baseEditor.on('scroll', function () {
            self.syncScroll(EventDirection.OUTGOING);
        });
        this.ownEditor.on('scroll', function () {
            self.syncScroll(EventDirection.INCOMING);
        });
    }
    /**
     * Sync scrolling between base and own editors. `type` is used to indicate
     * which editor is the source, and which editor is the destination of the sync.
     */
    syncScroll(type) {
        if (this.modelInvalid()) {
            return;
        }
        if (!this.lockScroll) {
            return;
        }
        // editor: What triggered event, other: What needs to be synced
        let editor;
        let other;
        if (type === EventDirection.OUTGOING) {
            editor = this.baseEditor;
            other = this.ownEditor;
        }
        else {
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
        window.requestAnimationFrame(function () {
            other.scrollTo(other.state.scrollPosition.left, other.state.scrollPosition.top);
            other.state.scrollTicking = false;
            other.state.scrollSetBy = self;
        });
        other.state.scrollTicking = true;
        return;
    }
    updateMarks(editor, diff, markers, type) {
        let classes;
        if (this.classes === null) {
            // Only store prefixes here, will be completed later
            classes = util_1.copyObj(mergeClassPrefix);
        }
        else {
            classes = this.classes;
        }
        let self = this;
        function markChunk(editor, from, to, sources) {
            if (self.classes === null && sources.length > 0) {
                // Complete merge class prefixes here
                classes = util_1.copyObj(mergeClassPrefix);
                // First, figure out 'action' state of chunk
                let s = sources[0].action;
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
                        picker.sources = sources;
                        picker.classList.add(GUTTER_PICKER_CLASS);
                        editor.setGutterMarker(line, GUTTER_PICKER_CLASS, picker);
                    }
                    else if (editor === self.baseEditor) {
                        for (let s of sources) {
                            if (s.decision.action === 'custom' &&
                                !util_1.hasEntries(s.decision.localDiff) &&
                                !util_1.hasEntries(s.decision.remoteDiff)) {
                                // We have a custom decision, add picker on base only!
                                let picker = elt('div', PICKER_SYMBOL, classes.gutter);
                                picker.sources = sources;
                                picker.classList.add(GUTTER_PICKER_CLASS);
                                editor.setGutterMarker(line, GUTTER_PICKER_CLASS, picker);
                            }
                        }
                    }
                    else if (conflict && editor === self.ownEditor) {
                        // Add conflict markers on editor, if conflicted
                        let conflictMarker = elt('div', CONFLICT_MARKER, '');
                        conflictMarker.sources = sources;
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
                    picker.sources = sources;
                    picker.classList.add(GUTTER_PICKER_CLASS);
                    editor.setGutterMarker(line, GUTTER_PICKER_CLASS, picker);
                }
                else if (conflict) {
                    // Add conflict markers on editor, if conflicted
                    let conflictMarker = elt('div', CONFLICT_MARKER, '');
                    conflictMarker.sources = sources;
                    conflictMarker.classList.add(GUTTER_CONFLICT_CLASS);
                    editor.setGutterMarker(line, GUTTER_CONFLICT_CLASS, conflictMarker);
                }
                editor.addLineClass(line, 'background', classes.end + '-empty');
                markers.push(line);
            }
        }
        let cls = type === DIFF_OP.DIFF_DELETE ? classes.del : classes.insert;
        editor.operation(function () {
            let edit = editor === self.baseEditor;
            if (self.classes) {
                clearMarks(editor, markers, classes);
            }
            else {
                clearMergeMarks(editor, markers);
            }
            highlightChars(editor, diff, markers, cls);
            for (let c of self.chunks) {
                if (edit) {
                    markChunk(editor, c.baseFrom, c.baseTo, c.sources);
                }
                else {
                    markChunk(editor, c.remoteFrom, c.remoteTo, c.sources);
                }
            }
        });
    }
    get ownEditor() {
        return this.ownWidget.cm;
    }
}
exports.DiffView = DiffView;
// Updating the marks for editor content
function clearMergeMarks(editor, arr) {
    for (let postfix of ['-local', '-remote', '-either', '-custom']) {
        let classes = util_1.copyObj(mergeClassPrefix);
        for (let k of Object.keys(classes)) {
            classes[k] += postfix;
        }
        clearMarks(editor, arr, classes);
    }
}
function isTextMarker(marker) {
    return 'clear' in marker;
}
function clearMarks(editor, arr, classes) {
    for (let i = arr.length - 1; i >= 0; --i) {
        let mark = arr[i];
        if (isTextMarker(mark)) {
            mark.clear();
            arr.splice(i, 1);
        }
        else if (mark.parent) {
            editor.removeLineClass(mark, 'background', classes.chunk);
            editor.removeLineClass(mark, 'background', classes.start);
            editor.removeLineClass(mark, 'background', classes.end);
            editor.removeLineClass(mark, 'background', CHUNK_CONFLICT_CLASS);
            // Merge editor does not set a marker currently, so don't clear for it:
            if (util_1.valueIn(classes.gutter, [leftClasses.gutter, rightClasses.gutter])) {
                editor.setGutterMarker(mark, GUTTER_PICKER_CLASS, null);
            }
            else {
                editor.setGutterMarker(mark, GUTTER_CONFLICT_CLASS, null);
            }
            let line = editor.lineInfo(mark);
            if (!line.bgClass || line.bgClass.length === 0) {
                arr.splice(i, 1);
            }
        }
    }
}
function highlightChars(editor, ranges, markers, cls) {
    let doc = editor.getDoc();
    let origCls = null;
    if (util_1.valueIn(cls, [mergeClassPrefix.del, mergeClassPrefix.insert])) {
        origCls = cls;
    }
    for (let r of ranges) {
        if (origCls !== null) {
            cls = origCls + (r.source ? '-' + r.source.action : '');
        }
        markers.push(doc.markText(r.from, r.to, { className: cls }));
    }
}
// Updating the gap between editor and original
/**
 * From a line in base, find the matching line in another editor by chunks.
 */
function getMatchingEditLine(baseLine, chunks) {
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
function getMatchingEditLineLC(toMatch, chunks) {
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
function findAlignedLines(dvs) {
    let linesToAlign = [];
    let ignored = [];
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
        }
        else {
            if (linesToAlign.length > 0) {
                let prev = linesToAlign[linesToAlign.length - 1];
                let diff = lines[0] - prev[0];
                for (let j = 1; j < lines.length; ++j) {
                    if (diff !== lines[j] - prev[j]) {
                        diff = null;
                        break;
                    }
                }
                if (diff === null) {
                    linesToAlign.push(lines);
                }
                else {
                    ignored.push(lines[0]);
                    continue;
                }
            }
            else {
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
                if (util_1.valueIn(chunk.baseTo, ignored)) {
                    // Chunk already consumed, continue to next chunk
                    j = -1;
                    break;
                }
                else if (align[0] >= chunk.baseTo) {
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
                    }
                    else {
                        lines.push(getMatchingEditLineLC(chunk, others[k].lineChunks));
                    }
                }
                if (linesToAlign.length > j && linesToAlign[j][0] === chunk.baseTo) {
                    let last = linesToAlign[j];
                    for (let k = 0; k < lines.length; ++k) {
                        last[k] = Math.max(last[k], lines[k]);
                    }
                }
                else {
                    linesToAlign.splice(j, 0, lines);
                }
            }
        }
    }
    return linesToAlign;
}
function alignLines(cm, lines, aligners) {
    let maxOffset = 0;
    let offset = [];
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
function padAbove(cm, line, size) {
    let above = true;
    if (line > cm.getDoc().lastLine()) {
        line--;
        above = false;
    }
    let elt = document.createElement('div');
    elt.className = 'CodeMirror-merge-spacer';
    elt.style.height = size + 'px';
    elt.style.minWidth = '1px';
    return cm.addLineWidget(line, elt, { height: size, above: above });
}
// Merge view, containing 1 or 2 diff views.
class MergeView extends widgets_1.Panel {
    constructor(options) {
        super();
        this.initialized = false;
        this.collapsedRanges = [];
        this.options = options;
        let remote = options.remote;
        let local = options.local || null;
        let merged = options.merged || null;
        let panes = 0;
        let left = this.left = null;
        let right = this.right = null;
        let merge = this.merge = null;
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
        let dvOptions = options;
        if (merged) {
            options.gutters = [GUTTER_CONFLICT_CLASS, GUTTER_PICKER_CLASS];
            if (options.lineWrapping === undefined) {
                // Turn off linewrapping for merge view by default, keep for diff
                options.lineWrapping = false;
            }
        }
        this.base = new editor_1.EditorWidget(options.value, util_1.copyObj({ readOnly: !!options.readOnly }, options));
        this.base.addClass('CodeMirror-merge-pane');
        this.base.addClass('CodeMirror-merge-pane-base');
        if (merged) {
            let showBase = options.showBase !== false;
            if (!showBase) {
                this.base.node.style.display = 'hidden';
            }
            let leftWidget;
            if (!local || local.remote === null) {
                // Local value was deleted
                left = this.left = null;
                leftWidget = new widgets_1.Widget({ node: elt('div', 'Value missing', 'jp-mod-missing') });
            }
            else {
                left = this.left = new DiffView(local, 'left', this.alignViews.bind(this), util_1.copyObj(dvOptions));
                this.diffViews.push(left);
                leftWidget = left.ownWidget;
            }
            leftWidget.addClass('CodeMirror-merge-pane');
            leftWidget.addClass('CodeMirror-merge-pane-local');
            this.addWidget(leftWidget);
            if (showBase) {
                this.addWidget(this.base);
            }
            let rightWidget;
            if (!remote || remote.remote === null) {
                // Remote value was deleted
                right = this.right = null;
                rightWidget = new widgets_1.Widget({ node: elt('div', 'Value missing', 'jp-mod-missing') });
            }
            else {
                right = this.right = new DiffView(remote, 'right', this.alignViews.bind(this), util_1.copyObj(dvOptions));
                this.diffViews.push(right);
                rightWidget = right.ownWidget;
            }
            rightWidget.addClass('CodeMirror-merge-pane');
            rightWidget.addClass('CodeMirror-merge-pane-remote');
            this.addWidget(rightWidget);
            this.addWidget(new widgets_1.Widget({
                node: elt('div', null, 'CodeMirror-merge-clear', 'height: 0; clear: both;')
            }));
            merge = this.merge = new DiffView(merged, 'merge', this.alignViews.bind(this), util_1.copyObj({ readOnly }, util_1.copyObj(dvOptions)));
            this.diffViews.push(merge);
            let mergeWidget = merge.ownWidget;
            mergeWidget.addClass('CodeMirror-merge-pane');
            mergeWidget.addClass('CodeMirror-merge-pane-final');
            this.addWidget(mergeWidget);
            panes = 3 + (showBase ? 1 : 0);
        }
        else if (remote) { // If in place for type guard
            this.addWidget(this.base);
            if (remote.unchanged || remote.added || remote.deleted) {
                if (remote.unchanged) {
                    this.base.addClass('CodeMirror-merge-pane-unchanged');
                }
                else if (remote.added) {
                    this.base.addClass('CodeMirror-merge-pane-added');
                }
                else if (remote.deleted) {
                    this.base.addClass('CodeMirror-merge-pane-deleted');
                }
                panes = 1;
            }
            else {
                right = this.right = new DiffView(remote, 'right', this.alignViews.bind(this), dvOptions);
                this.diffViews.push(right);
                let rightWidget = right.ownWidget;
                rightWidget.addClass('CodeMirror-merge-pane');
                rightWidget.addClass('CodeMirror-merge-pane-remote');
                this.addWidget(new widgets_1.Widget({ node: right.buildGap() }));
                this.addWidget(rightWidget);
                panes = 2;
            }
            this.addWidget(new widgets_1.Widget({
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
            this.base.cm.operation(function () {
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
    alignViews(force) {
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
        let self = this;
        let f = function () {
            // Clear old aligners
            let aligners = self.aligners;
            for (let i = 0; i < aligners.length; i++) {
                aligners[i].clear();
            }
            aligners.length = 0;
            // Editors (order is important, so it matches
            // format of linesToAlign)
            let cm = [self.base.cm];
            let scroll = [];
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
            f = function (fn) {
                return function () { self.base.cm.operation(fn); };
            }(f);
        }
        for (let dv of this.diffViews) {
            if (!dv.ownEditor.curOp) {
                f = function (fn) {
                    return function () { dv.ownEditor.operation(fn); };
                }(f);
            }
        }
        // Perform alignment
        f();
    }
    setShowDifferences(val) {
        if (this.right) {
            this.right.setShowDifferences(val);
        }
        if (this.left) {
            this.left.setShowDifferences(val);
        }
    }
    getMergedValue() {
        if (!this.merge) {
            throw new Error('No merged value; missing "merged" view');
        }
        return this.merge.ownEditor.getValue();
    }
}
exports.MergeView = MergeView;
function collapseSingle(cm, from, to) {
    cm.addLineClass(from, 'wrap', 'CodeMirror-merge-collapsed-line');
    let widget = document.createElement('span');
    widget.className = 'CodeMirror-merge-collapsed-widget';
    widget.title = 'Identical text collapsed. Click to expand.';
    let mark = cm.getDoc().markText(CodeMirror.Pos(from, 0), CodeMirror.Pos(to - 1), {
        inclusiveLeft: true,
        inclusiveRight: true,
        replacedWith: widget,
        clearOnEnter: true
    });
    function clear() {
        mark.clear();
        cm.removeLineClass(from, 'wrap', 'CodeMirror-merge-collapsed-line');
    }
    CodeMirror.on(widget, 'click', clear);
    return { mark: mark, clear: clear };
}
function collapseStretch(size, editors) {
    let marks = [];
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
        mark.mark.on('clear', clear);
    }
    return marks[0].mark;
}
function unclearNearChunks(dv, margin, off, clear) {
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
function collapseIdenticalStretches(mv, margin) {
    // FIXME: Use all panes
    if (typeof margin !== 'number') {
        margin = 2;
    }
    let clear = [];
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
                let editors = [{ line: line, cm: edit }];
                if (mv.left) {
                    editors.push({ line: getMatchingEditLine(line, mv.left.chunks),
                        cm: mv.left.ownEditor });
                }
                if (mv.right) {
                    editors.push({ line: getMatchingEditLine(line, mv.right.chunks),
                        cm: mv.right.ownEditor });
                }
                if (mv.merge) {
                    editors.push({ line: getMatchingEditLine(line, mv.merge.chunks),
                        cm: mv.merge.ownEditor });
                }
                let mark = collapseStretch(size, editors);
                mv.collapsedRanges.push({ line, size });
                mark.on('clear', () => {
                    for (let i = 0; i < mv.collapsedRanges.length; ++i) {
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
function elt(tag, content, className, style) {
    let e = document.createElement(tag);
    if (className) {
        e.className = className;
    }
    if (style) {
        e.style.cssText = style;
    }
    if (typeof content === 'string') {
        e.appendChild(document.createTextNode(content));
    }
    else if (content) {
        for (let i = 0; i < content.length; ++i) {
            e.appendChild((content)[i]);
        }
    }
    return e;
}
function findPrevDiff(chunks, start, isOrig) {
    for (let i = chunks.length - 1; i >= 0; i--) {
        let chunk = chunks[i];
        let to = (isOrig ? chunk.remoteTo : chunk.baseTo) - 1;
        if (to < start) {
            return to;
        }
    }
    return null;
}
function findNextDiff(chunks, start, isOrig) {
    for (let i = 0; i < chunks.length; i++) {
        let chunk = chunks[i];
        let from = (isOrig ? chunk.remoteFrom : chunk.baseFrom);
        if (from > start) {
            return from;
        }
    }
    return null;
}
var DiffDirection;
(function (DiffDirection) {
    DiffDirection[DiffDirection["Previous"] = -1] = "Previous";
    DiffDirection[DiffDirection["Next"] = 1] = "Next";
})(DiffDirection || (DiffDirection = {}));
function goNearbyDiff(cm, dir) {
    let found = null;
    let views = cm.state.diffViews;
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
    }
    else {
        return CodeMirror.Pass;
    }
}
CodeMirror.commands.goNextDiff = function (cm) {
    return goNearbyDiff(cm, DiffDirection.Next);
};
CodeMirror.commands.goPrevDiff = function (cm) {
    return goNearbyDiff(cm, DiffDirection.Previous);
};
//# sourceMappingURL=mergeview.js.map