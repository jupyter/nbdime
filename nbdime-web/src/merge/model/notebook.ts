// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
'use strict';

import {
  nbformat
} from '@jupyterlab/coreutils';

import {
  arraysEqual, valueIn, hasEntries, stableSort
} from '../../common/util';

import {
  IDiffAddRange, IDiffPatch, IDiffRemoveRange, IDiffArrayEntry,
  IDiffEntry
} from '../../diff/diffentries';

import {
  IMergeDecision, MergeDecision, resolveCommonPaths, filterDecisions,
  decisionSortKey
} from '../../merge/decisions';

import {
   labelSource
} from '../../chunking';

import {
  stringify
} from '../../patch';

import {
  CellMergeModel
} from './cell';

import {
  MetadataMergeModel
} from './metadata';


/**
 * Diff model for a Jupyter Notebook
 */
export
class NotebookMergeModel {

  static preprocessDecisions(rawMergeDecisions: IMergeDecision[]): MergeDecision[] {
    let mergeDecisions: MergeDecision[] = [];
    for (let rmd of rawMergeDecisions) {
      mergeDecisions.push(new MergeDecision(rmd));
    }
    mergeDecisions = splitCellChunks(mergeDecisions);
    mergeDecisions = splitCellRemovals(mergeDecisions);
    mergeDecisions = splitCellInsertions(mergeDecisions);
    mergeDecisions = splitCellListPatch(mergeDecisions);
    resolveCommonPaths(mergeDecisions);
    for (let md of mergeDecisions) {
      if (md.action === 'either') {
        labelSource(md.localDiff, {decision: md, action: 'either'});
        labelSource(md.remoteDiff, {decision: md, action: 'either'});
      } else {
        labelSource(md.localDiff, {decision: md, action: 'local'});
        labelSource(md.remoteDiff, {decision: md, action: 'remote'});
      }
      labelSource(md.customDiff, {decision: md, action: 'custom'});
    }
    return mergeDecisions;
  }

  /**
   * Create a new NotebookMergeModel from a base notebook and a list of
   * merge decisions.
   *
   * The base as well as the merge decisions are normally supplied by the
   * nbdime server.
   */
  constructor(base: nbformat.INotebookContent,
              rawMergeDecisions: IMergeDecision[]) {
    this.base = base;
    let ctor = this.constructor as typeof NotebookMergeModel;
    let decisions = ctor.preprocessDecisions(rawMergeDecisions);

    // The notebook metadata MIME type is used for determining the MIME type
    // of source cells, so store it easily accessible:
    let mimetype: string | undefined;
    try {
      mimetype = base.metadata.language_info!.mimetype;
    } catch (e) {
      // missing metadata(probably old notebook)
    }
    this.mimetype = mimetype || 'text/python';

    this.cells = this.buildCellList(decisions);

    let metadataDecs = filterDecisions(decisions, ['metadata']);
    this.metadata = new MetadataMergeModel(base.metadata, metadataDecs);
    this.unsavedChanges = false;
  }


  serialize(): nbformat.INotebookContent {
    let nb: any = {};
    // Simply copy all root-level fields except cells/metadata
    for (let key in this.base) {
      if (!valueIn(key, ['cells', 'metadata'])) {
        nb[key] = this.base[key];
      }
    }

    // Serialize metadata
    nb['metadata'] = this.metadata.serialize();

    // Serialzie cell list
    let cells: (nbformat.ICell | null)[] = [];
    for (let c of this.cells) {
      let s = c.serialize();
      if (s !== null) {
        cells.push(s);
      }
    }
    nb['cells'] = cells;

    // As long as base is a valid notebook, and sub-serialization is valid,
    // this output should be a valid notebook.
    return nb as nbformat.INotebookContent;
  }

  get decisions(): MergeDecision[] {
    let ret: MergeDecision[] = [];
    for (let c of this.cells) {
      ret = ret.concat(c.decisions);
    }
    ret = ret.concat(this.metadata.decisions);
    return ret;
  }

  get conflicts(): MergeDecision[] {
    let ret: MergeDecision[] = [];
    for (let md of this.decisions) {
      if (md.conflict) {
        ret.push(md);
      }
    }
    return ret;
  }

  /**
   * Base notebook of the merge
   */
  base: nbformat.INotebookContent;

  /**
   * List of individual cell merges
   */
  cells: CellMergeModel[];

  /**
   * Metadata merge model
   */
  metadata: MetadataMergeModel;

  /**
   * The default MIME type according to the notebook's root metadata
   */
  mimetype: string;

  /**
   * Whether there are unsaved changes
   */
  unsavedChanges: boolean;

  /**
   * Correlate the different cells in the diff lists into a merge list
   */
  protected buildCellList(decisions: MergeDecision[]): CellMergeModel[] {
    // We have to check for merge decisions on the `cells` object in
    // order to check for added cells. This assumes that the common
    // paths of the merge decisions have been resolved. It also assumes that
    // no merge decision can have root as its common path.

    // Create arrays of base value and decisions to match base cell list
    let cellDecisions: {base: any, decisions: MergeDecision[]}[] = [];
    for (let bc of this.base.cells) {
      // Create empty decisions array for now, add in below
      cellDecisions.push({base: bc, decisions: []});
    }

    let insertOffset = 0;
    // Assumes merge decisions come in order!
    for (let md of decisions) {
      let key = md.absolutePath;
      if (key.length < 1 || key[0] !== 'cells') {
        continue;   // Only care about decisions on cells here
      }

      if (arraysEqual(key, ['cells'])) {
        let idx: number | null = null;
        let insertion = false;
        for (let di of md.diffs) {
          // Ensure diff has exactly one item:
          if (!di || di.length === 0) {
            continue;
          }
          // All keys should be the same since we run splitCellChunks first
          idx = di[0].key as number;
          if (di[0].op === 'addrange') {
            // Insert entries into `cells` at idx
            let offsetIdx = insertOffset + idx;
            cellDecisions.splice(offsetIdx, 0, {base: null, decisions: [md]});
            insertOffset += 1;
            insertion = true;  // flag to break outer loop
            break;
          }
          // Only checking for insertions in this loop, since insertions can
          // only be paired with other insertions.
        }
        if (insertion) {
          continue;
        }
        // If we reach this point, it is not an insertion merge!
        if (idx === null) {
          throw new Error('No index could be found for merge decision!');
        }
        let cds = cellDecisions[idx + insertOffset].decisions;
        cds.push(md);
      } else {
        // Has a path into a cell
        // Format specifies that these always comes before decisions that
        // change the order of cells, so index is straight forward!
        let idx = key[1] as number;
        let cds = cellDecisions[idx].decisions;
        cds.push(md);
      }
    }

    let cells: CellMergeModel[] = [];
    for (let cellInfo of cellDecisions) {
      cells.push(new CellMergeModel(
        cellInfo.base, cellInfo.decisions, this.mimetype));
    }

    return cells;
  }
}


function isChunk(diff: IDiffEntry[] | null): diff is IDiffArrayEntry[] {
  return !!diff && diff.length === 2 &&
    diff[0].key === diff[1].key;
}

/**
 * The merge format allows for chunking of sequence diffs such that one entry
 * in the diff lists have 2 entries, where the first is always an insertion
 * (addrange). For cells, we split these decisions in two, for easier
 * visualization.
 */
function splitCellChunks(mergeDecisions: MergeDecision[]): MergeDecision[] {
  let output: MergeDecision[] = [];
  for (let md of mergeDecisions) {
    if (arraysEqual(md.absolutePath, ['cells'])) {
      if (md.localDiff && !md.remoteDiff) {
        for (let d of md.localDiff) {
          let nmd = new MergeDecision(md);
          nmd.localDiff = [d];
          output.push(nmd);
        }
      } else if (md.remoteDiff && !md.localDiff) {
        for (let d of md.remoteDiff) {
          let nmd = new MergeDecision(md);
          nmd.absolutePath = md.absolutePath.slice();
          nmd.remoteDiff = [d];
          output.push(nmd);
        }
      } else if (isChunk(md.localDiff)) {
        // Split off local
        output.push(new MergeDecision(
          md.absolutePath.slice(),
          md.localDiff.slice(0, 1),
          [],
          'local', // Check for custom action first?
          md.conflict
        ));
        let nmd = new MergeDecision(md);
        nmd.localDiff = md.localDiff.slice(1);
        output.push(nmd);
      } else if (isChunk(md.remoteDiff)) {
        // Split off remote
        output.push(new MergeDecision(
          md.absolutePath.slice(),
          [],
          md.remoteDiff.slice(0, 1),
          'remote', // Check for custom action first?
          md.conflict
        ));
        let nmd = new MergeDecision(md);
        nmd.remoteDiff = md.remoteDiff.slice(1);
        output.push(nmd);
      } else {
        output.push(md);  // deepCopy?
      }
    } else {
      output.push(md);
    }
  }
  resolveCommonPaths(output);
  return output;
}


/**
 * If any decisions have diffs on different cells, split them
 * up for one decision per cell.
 */
function splitCellListPatch(mergeDecisions: MergeDecision[]): MergeDecision[] {
  let output: MergeDecision[] = [];

  for (let md of mergeDecisions) {
    if (!arraysEqual(md.absolutePath, ['cells'])) {
      output.push(md);
      continue;
    }
    // Null out empty diffs
    let dl = hasEntries(md.localDiff) ? md.localDiff : null;
    let dr = hasEntries(md.remoteDiff) ? md.remoteDiff : null;

    if (dl && dl.length < 2 && dr && dr.length < 2) {
      // Single cell affected
      output.push(md);
      continue;
    }

    // Before this is called, we should have split up chunks
    // as well as range addition/removal, so all diffs
    // should have different keys
    let maxlen = Math.max(dl ? dl.length : 0, dr ? dr.length : 0);
    for (let i = 0; i < maxlen; ++i) {
      let subdl = dl && i < dl.length ? [dl[i]] : null;
      let subdr = dr && i < dr.length ? [dr[i]] : null;
      output.push(new MergeDecision(
        md.absolutePath.slice(),
        subdl,
        subdr,
        md.action,
        md.conflict
        ));
    }
  }
  return stableSort(output, decisionSortKey);
}


/**
 * Split "removerange" diffs on cell list level into individual decisions!
 */
function splitCellRemovals(mergeDecisions: MergeDecision[]): MergeDecision[] {
  let output: MergeDecision[] = [];

  let makeSplitPart = function(md: MergeDecision, key: number,
                               local: boolean, remote: boolean): MergeDecision {
    let newMd = new MergeDecision(md.absolutePath.slice(), null, null,
                                  md.action, md.conflict);
    let newDiff: IDiffRemoveRange[] = [{
        key: key,
        op: 'removerange',
        length: 1
    }];
    console.assert(local || remote);
    if (local) {
      newMd.localDiff = newDiff;
    }
    if (remote) {
      newMd.remoteDiff = newDiff;
    }
    return newMd;
  };

  for (let md of mergeDecisions) {
    if (!arraysEqual(md.absolutePath, ['cells'])) {
      output.push(md);
      continue;
    }

    let dl = hasEntries(md.localDiff) ? md.localDiff[md.localDiff.length - 1] as IDiffArrayEntry : null;
    let dr = hasEntries(md.remoteDiff) ? md.remoteDiff[md.remoteDiff.length - 1] as IDiffArrayEntry : null;
    // TODO: Does it make sense to split on custom?

    if (dl && !dr || dr && !dl) {
      // One-way diff
      let d = (dl ? dl : dr!);

      if (d.op === 'removerange' && d.length > 1) {
        // Found a one-way diff to split!
        for (let i = 0; i < d.length; ++i) {
          output.push(makeSplitPart(md, d.key + i, !!dl, !!dr));
        }
      } else {
        // Not a removerange type:
        output.push(md);
        continue;
      }
    } else if (dr && dl) {
      // Two way diff, keys need to be matched
      if (dl.op !== 'removerange' && dr.op !== 'removerange') {
        // Not a removerange type:
        output.push(md);
        continue;
      } else if (dl.op === dr.op) {
        // Both sides have removerange, just match keys/length
        // Note: Assume that ranges have overlap, since they are in one decision
        let klStart = dl.key;
        let krStart = dr.key;
        let start = Math.min(klStart, krStart);
        let klEnd = klStart + (dl as IDiffRemoveRange).length;
        let krEnd = krStart + (dr as IDiffRemoveRange).length;
        let end = Math.max(klEnd, krEnd);
        for (let i = start; i < end; ++i) {
          let local = i >= klStart && i < klEnd;
          let remote = i >= krStart && i < krEnd;
          output.push(makeSplitPart(md, i, local, remote));
        }
      } else {
        // One side has removerange, the other a patch op (implied)
        let remLocal = dl.op === 'removerange';
        let rOp = (remLocal ? dl : dr) as IDiffRemoveRange;
        let pOp = (remLocal ? dr : dl) as IDiffPatch;
        console.assert(pOp.op === 'patch');

        let pidx = pOp.key;
        let start = rOp.key;
        for (let i = start; i < start + rOp.length; ++i) {
          let newMd = makeSplitPart(md, i, remLocal, !remLocal);
          if (i === pidx) {
            if (remLocal) {
              newMd.remoteDiff = [pOp];
            } else  {
              newMd.localDiff = [pOp];
            }
          }
          output.push(newMd);
        }
      }
    }
  }
  return output;
}


/**
 * Split "addrange" diffs on cell list level into individual decisions!
 * Also splits two-way insertions into two individual ones.
 */
function splitCellInsertions(mergeDecisions: MergeDecision[]): MergeDecision[] {
  let output: MergeDecision[] = [];

  let makeSplitPart = function(md: MergeDecision, value: any,
                               local: boolean, remote: boolean): MergeDecision {
    let newMd = new MergeDecision(md.absolutePath.slice(), null, null,
                                  md.action, md.conflict);
    if ((local && !hasEntries(md.localDiff)) || (!local && !hasEntries(md.remoteDiff))) {
      throw new Error('Invalid input: ' + md);
    }
    let key = (local ? md.localDiff : md.remoteDiff)![0].key as number;
    let newDiff: IDiffAddRange[] = [{
        key: key,
        op: 'addrange',
        valuelist: [value]
    }];

    console.assert(local || remote);
    if (local) {
      newMd.localDiff = newDiff;
    }
    if (remote) {
      newMd.remoteDiff = newDiff;
    }
    return newMd;
  };

  for (let md of mergeDecisions) {
    // Just push decisions not on cells list:
    if (!arraysEqual(md.absolutePath, ['cells'])) {
      output.push(md);
      continue;
    }

    // Check wether all diffs are pure addrange
    let correctType = true;
    if (md.localDiff) {
      for (let dl of md.localDiff) {
        if (dl.op !== 'addrange') {
          correctType = false;
          break;
        }
      }
    }
    if (md.remoteDiff) {
      for (let dl of md.remoteDiff) {
        if (dl.op !== 'addrange') {
          correctType = false;
          break;
        }
      }
    }
    if (!correctType) {
      output.push(md);
      continue;
    }

    let dl = md.localDiff && md.localDiff.length === 1 ? md.localDiff[0] as IDiffAddRange : null;
    let dr = md.remoteDiff && md.remoteDiff.length === 1 ? md.remoteDiff[0] as IDiffAddRange : null;

    if (dl && !dr || dr && !dl) {
      // One-way diff
      let d = (dl ? dl : dr!);
      let insert = d.valuelist;
      for (let v of insert) {
        output.push(makeSplitPart(md, v, !!dl, !!dr));
      }
    } else if (dl && dr) {
      // Two way diff
      // First, check if both insertions are equal!
      let eq = stringify(dl.valuelist) === stringify(dr.valuelist);
      if (eq) {
        // Split to one decision per cell
        for (let c of dl.valuelist) {
          output.push(makeSplitPart(md, c, true, true));
        }
      } else {
        // Next, check decision for ruling on order (e.g.
        // local_then_remote, which we will use as the default).

        let start = dl.key;
        console.assert(start === dr.key);
        if (md.action === 'remote_then_local') {
          // Only case where we need to switch order!
          for (let c of dr.valuelist as any[]) {
            output.push(makeSplitPart(md, c, false, true));
          }
          for (let c of dl.valuelist as any[]) {
            output.push(makeSplitPart(md, c, true, false));
          }
        } else {
          for (let c of dl.valuelist as any[]) {
            output.push(makeSplitPart(md, c, true, false));
          }
          for (let c of dr.valuelist as any[]) {
            output.push(makeSplitPart(md, c, false, true));
          }
        }
      }

    }
  }
  return output;
}
