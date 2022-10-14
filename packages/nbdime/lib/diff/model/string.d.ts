import * as nbformat from '@jupyterlab/nbformat';
import { JSONObject, JSONArray, JSONValue, PartialJSONObject } from '@lumino/coreutils';
import { IDiffEntry } from '../diffentries';
import { DiffRangeRaw, DiffRangePos } from '../range';
import { Chunk } from '../../chunking';
import { IDiffModel } from './common';
/**
 * Interface for a string diff model.
 *
 * String diff models are used for any content where the final
 * diff should be presented as a difference between strings
 * (as compared to e.g. images). As such, it is NOT restricted
 * to cases where original content is in a string format.
 */
export interface IStringDiffModel extends IDiffModel {
    /**
     * Base value
     */
    base: string | null;
    /**
     * Remote value
     */
    remote: string | null;
    /**
     * Mimetype of the data the string represents.
     *
     * Can be used for things such as syntax highlighting.
     */
    mimetype: string;
    /**
     * Location of additions, as positions in the remote value.
     *
     * Locations should be sorted on the ranges' `from` position
     */
    additions: DiffRangePos[];
    /**
     * Location of deletions, as positions in the base value.
     *
     * Locations should be sorted on the ranges' `from` position
     */
    deletions: DiffRangePos[];
    /**
     * A function that will separate the diff into chunks.
     */
    getLineChunks(): Chunk[];
    /**
     * Create an iterator for iterating over the diffs in order
     */
    iterateDiffs(): StringDiffModel.DiffIter;
}
/**
 * Standard implementation of the IStringDiffModel interface.
 */
export declare class StringDiffModel implements IStringDiffModel {
    base: string | null;
    remote: string | null;
    /**
     * StringDiffModel constructor.
     *
     * Will translate additions and deletions from absolute
     * coordinates, into {line, ch} based coordinates.
     * Both should be sorted on the `from` position before passing.
     *
     * Collapsible and collapsed both defaults to false.
     */
    constructor(base: string | null, remote: string | null, additions: DiffRangeRaw[], deletions: DiffRangeRaw[], collapsible?: boolean, header?: string, collapsed?: boolean);
    iterateDiffs(): StringDiffModel.DiffIter;
    /**
     * Chunk additions/deletions into line-based chunks
     */
    getLineChunks(): Chunk[];
    get unchanged(): boolean;
    get added(): boolean;
    get deleted(): boolean;
    collapsible: boolean;
    collapsibleHeader: string;
    startCollapsed: boolean;
    mimetype: string;
    additions: DiffRangePos[];
    deletions: DiffRangePos[];
}
export declare namespace StringDiffModel {
    type DiffIterValue = {
        range: DiffRangePos;
        isAddition: boolean;
    } | undefined;
    interface IIterator<T> {
        next(): T | undefined;
    }
    class DiffIter implements IIterator<DiffIterValue> {
        constructor(model: IStringDiffModel);
        next(): DiffIterValue | undefined;
        editOffset: number;
        done: boolean;
        protected model: IStringDiffModel;
        protected ia: number;
        protected id: number;
        protected hintTakeDeletion: boolean;
    }
    class SyncedDiffIter implements IIterator<DiffIterValue> {
        static cmp(a: DiffIterValue, b: DiffIterValue, offsetA: number, offsetB: number): 0 | 1 | -1;
        constructor(models: (IStringDiffModel | null)[]);
        next(): DiffIterValue;
        currentModel(): IStringDiffModel;
        currentOffset: number;
        protected i: number;
        protected models: IStringDiffModel[];
        protected iterators: DiffIter[];
        protected values: DiffIterValue[];
        protected offsets: number[];
    }
}
/**
 * Creates a StringDiffModel based on a patch operation.
 *
 * If base is not a string, it is assumed to be a JSON object/array,
 * and it will be stringified according to JSON stringification
 * rules.
 */
export declare function createPatchStringDiffModel(base: string | JSONObject | JSONArray | PartialJSONObject, diff: IDiffEntry[]): StringDiffModel;
/**
 * Factory for creating cell diff models for added, removed or unchanged content.
 *
 * If base is null, it will be treated as added, if remote is null it will be
 * treated as removed. Otherwise base and remote should be equal, represeting
 * unchanged content.
 */
export declare function createDirectStringDiffModel(base: JSONValue | null, remote: JSONValue | null): StringDiffModel;
/**
 * Assign MIME type to an IStringDiffModel based on the cell type.
 *
 * The parameter nbMimetype is the MIME type set for the entire notebook, and is
 * used as the MIME type for code cells.
 */
export declare function setMimetypeFromCellType(model: IStringDiffModel, cell: nbformat.ICell, nbMimetype: string): void;
//# sourceMappingURL=string.d.ts.map