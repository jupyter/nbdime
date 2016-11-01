// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
'use strict';

import {
  nbformat
} from '@jupyterlab/services';

import {
  DecisionPath, MergeDecision
} from './decisions';

import {
   labelSource
} from '../chunking';

import {
  IDiffEntry, IDiffAddRange, IDiffRemoveRange, IDiffPatch, IDiffArrayEntry,
  IDiffPatchArray, DiffCollection, opAddRange, opRemoveRange, opPatch,
  deepCopyDiff
} from '../diff/diffentries';

import {
  IStringDiffModel
} from '../diff/model';

import {
  getSubDiffByKey
} from '../diff/util';

import {
  raw2Pos
} from '../diff/range';

import {
  patchStringified
} from '../patch';

import {
  hasEntries
} from '../common/util';

import {
  CellMergeModel
} from './model';

import {
  getPathForNewDecision
} from './util';


/**
 * Replace the content of an array with another, in-place
 */
function replaceArrayContent<T>(array: T[], content: T[], start?: number, end?: number): void {
  if (array === content && start === undefined && end === undefined) {
    return;  // No-op
  }
  start = start || 0;
  if (end === undefined) {
    end = array.length - start;
  }
  array.splice.apply(array, ([start, end] as any[]).concat(content));
}

function isCellSimpleDeletion(cell: CellMergeModel): boolean {
  let ret = cell.local && cell.local.deleted &&
    (cell.remote === null || cell.remote.unchanged) ||  // Onesided deletion (other side unchanged)
    cell.remote && cell.remote.deleted &&
    (cell.local === null || cell.local.unchanged) ||  // Onesided deletion (other side unchanged)
    cell.local && cell.remote &&
    cell.local.deleted && cell.remote.deleted;  // Deletion on both
  return !!ret;
}


/**
 * Get the last diff, or, if the last diff is a removerange
 * and two last diffs share the same key, the addrange.
 */
function getLastDiffAddRange(diff: AddRem[]): IDiffAddRange | null {
  if (diff.length === 0) {
    return null;
  }
  let e = diff[diff.length - 1];
  // If last op is removal, check if preceding op is addition
  // on same key!
  if (e.op === 'removerange' &&
      diff.length > 1 && diff[diff.length - 2].key === e.key) {
    // Use preceding addrange as candidate
    e = diff[diff.length - 2];
  }
  return e.op === 'addrange' ? e : null;
}

/**
 * Whether both local and remote of the cell are unchanged.
 *
 * Note that this does not check whether the merge model is
 * unchanged!
 */
function isCellUnchanged(cell: CellMergeModel): boolean {
  let ret = cell.local && cell.local.unchanged &&
    cell.remote && cell.remote.unchanged;
  return !!ret;
}

export
interface IUpdateModelOptions {
  model: IStringDiffModel;

  full: string;

  baseLine: number;

  editCh: number;

  editLine: number;

  oldval: string[];

  newval: string[];
}

type AddRem = IDiffAddRange | IDiffRemoveRange;

/**
 * Converts any patch ops to an addrange/removerange pair
 */
function convertPatchOps(diff: IDiffArrayEntry[], options: IUpdateModelOptions): AddRem[] {
  // This function is optimized for maximal performance
  // when there are no patch ops (most common case)
  let anyPatch = false;
  for (let e of diff) {
    if (e.op === 'patch') {
      anyPatch = true;
      break;
    }
  }
  if (!anyPatch) {
    return diff as AddRem[];
  }
  let lineoffset = 0;
  let lines = options.model.base!.match(/^.*(\r\n|\r|\n|$)/gm)!;
  let ret: AddRem[] = [];
  for (let i=0; i < diff.length; ++i) {
    let e = diff[i];
    if (e.op === 'patch') {
      if (i > 0 && diff[i - 1].key === e.key &&
          diff[i - 1].source === e.source) {
        let d = diff[i - 1] as IDiffAddRange;
        let vl = d.valuelist as string[];
        // Previous diff was also on this key, merge addranges
        vl.push(lines[e.key + lineoffset]);
        // Add removerange
        let drr = opRemoveRange(e.key, 1);
        drr.source = e.source;
        ret.push(drr);
      } else {
        let dar = opAddRange(e.key, lines.slice(
            e.key + lineoffset, e.key + lineoffset + 1));
        let drr = opRemoveRange(e.key, 1);
        dar.source = drr.source = e.source;
        ret = ret.concat([dar, drr]);
      }
    } else {
      ret.push(e);
      if (e.op === 'addrange') {
        lineoffset += e.valuelist.length;
      } else {
        lineoffset -= e.length;
      }
    }
  }
  return ret;
}

function getPartials(diff: AddRem[], options: IUpdateModelOptions, startOffset: number, endOffset: number): {
    before: string[], after: string[], linediff: number, key: number } {
  let line = options.baseLine;
  let ch = options.editCh;
  let {oldval, newval} = options;
  let lines: string[] | null = null;
  let key = line;
  let linediff = 0;

  let lastAddedLine = newval[newval.length - 1];
  let lastDeletedLine = oldval[oldval.length - 1];

  let partialStart = ch > 0;
  let fullDeleteEnd = oldval.length > 1 && lastDeletedLine === '';
  let fullLineInsertions = ch === 0 && newval.length > 0 && lastAddedLine === '';

  let before: string[] = [''];
  let after: string[] | null = null;

  // Check for overlap with first diff:
  let firstDiff = diff[0];
  if (firstDiff && firstDiff.key <= line && firstDiff.op === 'addrange') {
    let vlLine = options.editLine - (firstDiff.key + startOffset);
    // Shift start forward:
    key = firstDiff.key;
    let vl = firstDiff.valuelist as string[];
    // Include any lines before edit:
    before = vl.slice(0, vlLine);
    // Add partial line
    before.push(
      partialStart ? vl[vlLine].slice(0, ch) : ''
    );
  } else if (partialStart) {
    // Replace previously unedited line:
    lines = options.full.match(/^.*(\r\n|\r|\n|$)/gm)!;
    before = [lines[options.editLine].slice(0, ch)];
    // Indicate that one unedited line should be removed
    linediff = 1;
  }

  // Check for overlap with last diff:
  let lastDiff = getLastDiffAddRange(diff);
  if (lastDiff) {
    let diffEditStart = lastDiff.key + endOffset;
    let matchLine = (options.editLine - diffEditStart) + oldval.length - 1;
    if (lastDeletedLine === '' && oldval.length > 1) {
      matchLine -= 1;
    }
    if (matchLine >= 0 && matchLine < lastDiff.valuelist.length) {
      let vl = lastDiff.valuelist as string[];
      // Figure out which bits to keep:
      let cut = lastDeletedLine.length;
      // If edit on one line, skip part before edit also
      if (oldval.length === 1) {
        cut += ch;
      }
      // Add partial line
      after = [vl[matchLine].slice(cut)];
      // Include any lines after edit
      after = after.concat(vl.slice(matchLine + 1));
    }
  }
  if (!after && !fullDeleteEnd && !fullLineInsertions) {
    // Add remains of previously unedited line
    if (lines === null) {
      lines = options.full.match(/^.*(\r\n|\r|\n|$)/gm)!;
    }
    let fullLine = lines[options.editLine + newval.length - 1];
    let cut = lastAddedLine.length;
    if (newval.length === 1) {
      cut += ch;
    }
    after = [fullLine.slice(cut)];
    // Indicate that an unedited line was replaced, but
    // check if this line was also taken into account above.
    if (oldval.length > 1) {
      linediff += 1;
    } else {
      linediff = 1;
    }
  }
  return {before, after: after || [''], linediff, key};
}

function joinPartials(a: string[], b: string[]): string[] {
  let joined = a.concat(b.slice(1));
  let iend = a.length - 1;
  joined[iend] = joined[iend].concat(b[0]);
  return joined;
}

/**
 * Get addrange to represent inserted text as well as any overlapping additions
 */
function getAddOp(diff: AddRem[], options: IUpdateModelOptions, startOffset: number, endOffset: number):
    { addop: IDiffAddRange | null, linediff: number} {
  let newval = options.newval;
  let newValuelist: string[];

  let {before, after, linediff, key} = getPartials(
    diff, options, startOffset, endOffset);

  newValuelist = joinPartials(before, newval);
  newValuelist = joinPartials(newValuelist, after);

  if (newValuelist.length === 1 && newValuelist[0].length === 0) {
    return {addop: null, linediff};
  } else if (newValuelist[newValuelist.length - 1].length === 0) {
    newValuelist.pop();
  }
  return {addop: opAddRange(key, newValuelist), linediff};
}

function getRemOp(diff: AddRem[], options: IUpdateModelOptions, extraLinediff: number): IDiffRemoveRange | null {
  let oldval = options.oldval;
  let line = options.baseLine;
  let linediff = extraLinediff;

  if (oldval.length > 1 || oldval[0].length > 0) {
    // Reduce the deletions to only those that were not
    // previously added by diff:
    let deletions = removeAddedDeletions(diff, options);
    linediff += deletions.length - 1;
  }

  // Set up removerange for all affected lines:
  let remop = opRemoveRange(line, linediff);

  // Next, extend remove op to replace overlapping removes
  mergeOverlappingRemoves(remop, diff);

  if (remop.length === 0) {
    return null;
  }
  return remop;
}

/**
 * Remove deletions that were added through an addrange.
 *
 * All diffs passed should overlap at least partially with
 * the edit!
 *
 * Returns options.oldval without those lines that were added by diff.
 */
function removeAddedDeletions(diff: AddRem[], options: IUpdateModelOptions): string[] {
  let offset = 0;
  let line = options.baseLine;
  let ret = options.oldval.slice();  // Copy
  let origLength = ret.length;
  for (let e of diff) {
    if (e.op !== 'addrange') {
      continue;
    }
    // All passed diffs overlap at least partially!
    let overlapStart = Math.max(e.key, line);
    let overlapEnd = Math.min(e.key + e.valuelist.length, line + origLength);
    let overlap = overlapEnd - overlapStart;
    ret.splice(Math.max(e.key - line - offset, 0), overlap);
    offset += overlap;
  }
  if (ret.length === 0) {
    ret = [''];
  }
  return ret;
}

function mergeOverlappingRemoves(remop: IDiffRemoveRange, diff: AddRem[]): void {
  for (let e of diff) {
    if (e.op === 'removerange') {
      // Extend end of diff
      remop.length += e.length;
    }
  }
}


function findDeletionOverlap(diff: AddRem[], options: IUpdateModelOptions): number[] {
  let editLength = options.oldval.length;
  let {baseLine, editLine} = options;
  let start = 0;
  let end = diff.length;
  let startOffset = 0;
  let endOffset = 0;
  let previousOffset = 0;
  for (let i=0; i < diff.length; ++i) {
    let e = diff[i];
    if (e.key < baseLine && (e.op !== 'addrange' ||
        e.key + startOffset + e.valuelist.length <= editLine)) {
      // Before start of edit
      ++start;
      startOffset += e.op === 'addrange' ? e.valuelist.length : -e.length;
    } else if (e.key + endOffset >= baseLine + editLength) {
      // After end of edit
      end = i;
      break;
    } else {
      // Op within edit, adjust offset to find end
      if (e.op === 'addrange') {
        previousOffset = 0;
        if (i + 1 < diff.length && diff[i + 1].key === e.key) {
          // Next op is on same key (know/assume removerange)
          // it should therefore also be within edit
          let d = diff[++i] as IDiffRemoveRange;
          endOffset -= d.length;
          previousOffset -= d.length;
        }
        endOffset += e.valuelist.length;
        previousOffset += e.valuelist.length;
      } else { // removerange
        endOffset -= e.length;
        previousOffset = e.length;
      }
    }
  }
  endOffset -= previousOffset;
  return [start, end, startOffset, endOffset];
}

/**
 * Update a diff with an edit, in-place
 */
function updateDiff(diffToUpdate: IDiffArrayEntry[], options: IUpdateModelOptions): void {
  let diff = convertPatchOps(diffToUpdate, options);

   // First, figure out which part of the diff is overlapping with edit:
  let [start, end, startOffset, endOffset] = findDeletionOverlap(diff, options);
  let overlappingDiff = diff.slice(start, end);

  // All overlapping diffs should be replaced by at maximum
  // a single addrange, and a single removerange

  // Find remains of any partial line deletions
  let {addop, linediff} = getAddOp(overlappingDiff, options, startOffset, endOffset);
  let remop = getRemOp(overlappingDiff, options, linediff);

  // Align start
  if (addop && remop) {
    addop.key = remop.key = Math.min(addop.key, remop.key);
  }

  // Sanity check:
  if (!addop && !remop) {
    throw new Error(
      'An edit should result in at least one diff operation');
  }

  // Replace back in overlapping diff
  let newop: AddRem[] = [];
  if (addop) {
    newop.push(addop);
  }
  if (remop) {
    newop.push(remop);
  }
  replaceArrayContent(diff, newop, start, end);
  replaceArrayContent(diffToUpdate, diff);
}

/**
 * Updates an inserted cell.
 *
 * Inserted cells have a single action:
 *  side A: null
 *  side B: addrange with a single ICell
 *  custom: addrange with a single, edited ICell
 */
function updateInsertedCell(options: IUpdateModelOptions): void {
  let model = options.model;
  let full = options.full;
  let cell = model.parent as CellMergeModel;
  let path = getPathForNewDecision(model);
  let subkey = path[1];
  if (cell.decisions.length !== 1) {
    throw new Error('Unexpected length of model\'s decisions');
  }
  if (model.additions.length !== 1) {
    throw new Error('Unexpected length of added models additions field');
  }

  // Update additions:
  let lines = full.match(/^.*(\r\n|\r|\n|$)/gm)!;
  model.additions[0].to.line = lines.length - 1;
  model.additions[0].to.ch = lines[lines.length - 1].length;

  // Update decision:
  let dec = cell.decisions[0];
  dec.action = 'custom';
  let diff = dec.customDiff;
  if (!hasEntries(diff)) {
    diff = hasEntries(dec.localDiff) ? dec.localDiff : dec.remoteDiff!;
    dec.customDiff = diff = deepCopyDiff(diff);
  }
  // We can now modify diff in place to update decision
  let cellVal = (diff[0] as IDiffAddRange).valuelist[0] as nbformat.ICell;
  cellVal[subkey![0]] = full;
}

/**
 * Updates a deleted cell.
 *
 * Deleted cell have a single action:
 *  side A: deleted,
 *  side B: unchanged
 *  custom: manual edits
 *
 * This cannot be changed, so we simply update the decision
 * on cell level
 */
function updateDeletedCell(options: IUpdateModelOptions): void {
  // Patch deleted model
    // Update diff on decision
    // Use diff to find additions/deletions
  let model = options.model;
  let cell = model.parent as CellMergeModel;
  let path = getPathForNewDecision(model);

  let dec = cell.decisions[0];
  let diff: IDiffArrayEntry[];
  // Ensure we got a diff:
  if (!hasEntries(dec.customDiff)) {
    diff = [];
    dec.customDiff = [opPatch(path[0][1], [opPatch(path[0][2], diff)])];
  } else {
    let celldiff = (dec.customDiff[0] as IDiffPatch).diff!;
    let subdiff = getSubDiffByKey(celldiff, path[0][2]);
    if (subdiff !== null) {
      diff = subdiff as IDiffArrayEntry[];
    } else {
      diff = [];
      celldiff.push(opPatch(path[0][2], diff));
    }
  }
  // Update diff with changes
  updateDiff(diff, options);
  labelSource(diff, {decision: dec, action: 'custom'});

  // Update additions/deletions
  let out = patchStringified(model.base || '', diff);
  model.additions = raw2Pos(out.additions, out.remote);
  model.deletions = raw2Pos(out.deletions, model.base || '');
  dec.action = 'custom';
}

/**
 * Updates an unchanged cell.
 *
 * Unchanged cells have no actions initially:
 *  local: unchanged
 *  remote: unchanged
 *  custom: unchanged OR multiple decisions with manual edits
 */
function updatedUnchangedCell(options: IUpdateModelOptions): void {
  // All decisions are custom
  patchPatchedModel(options, 'custom');
}

/**
 * Updates a patched cell.
 *
 * Pathced cells have more complex structure:
 *  local: deleted, patched or unchanged
 *  remote: deleted, patched or unchanged
 *  custom: patched, possibly with both manual edits and other changes
 *
 * Note that only one side can be deleted/unchanged at the same time.
 */
function updatedPatchedCell(options: IUpdateModelOptions): void {
  // Decisions might not all be custom
  patchPatchedModel(options, 'all');
}

function patchPatchedModel(options: IUpdateModelOptions, diffs: 'all' | 'custom') {
  // Patch model
    // Update remote
    // Find overlapping decisions (arg specifies which diffs to consider)
      // Add/replace custom diff (action -> custom)
    // Add new decisions (on subkey)
  let model = options.model;
  let cell = model.parent as CellMergeModel;
  let path = getPathForNewDecision(model);

  // Find overlapping decisions
    // Add custom diff if needed
    // Replace custom diff if existing
    // Set action to custom
  // Add new decisions for changes that do no overlap
}

export
function updateModel(options: IUpdateModelOptions) {
  let model = options.model;
  let cell = model.parent as CellMergeModel;
  // Update replaced value to include newlines as apropriate:
  let oldval = options.oldval;
  if (oldval.length > 1 || oldval[0].length > 0) {
    for (let i=0; i < oldval.length - 1; ++i) {
      if (oldval[i][oldval[i].length - 1] !== '\n') {
        oldval[i] = oldval[i] + '\n';
      }
    }
  }
  let newval = options.newval;
  if (newval.length > 1 || newval[0].length > 0) {
    for (let i=0; i < newval.length - 1; ++i) {
      newval[i] = newval[i] + '\n';
    }
  }

  // Update remote:
  model.remote = options.full;

  // If edited, cell should not be marked for deletion
  if (cell.deleteCell) {
    cell.deleteCell = false;
  }
  if (model.added) {
    // Inserted cell
    updateInsertedCell(options);
  } else if (isCellSimpleDeletion(cell)) {
    // Simple deletion
    updateDeletedCell(options);
  } else if (isCellUnchanged(cell)) {
    // Local and remote both unchanged, all decisions are custom
    updatedUnchangedCell(options);
  } else {
    updatedPatchedCell(options);
  }
}
