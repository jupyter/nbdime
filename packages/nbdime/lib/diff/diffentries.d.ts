import { ChunkSource } from '../chunking';
/**
 * The different diff operations available
 */
export declare type DiffOp = 'add' | 'remove' | 'replace' | 'patch' | 'addrange' | 'removerange';
/**
 * Base interface for all diff entries
 */
export interface IDiffEntryBase {
    /**
     * The key of the diff entry: Either the field name in an object, or the
     * index in a list/string.
     */
    key: string | number;
    /**
     * A string identifying the diff operation type, as defined by DiffOp.
     */
    op: DiffOp;
    /**
     * Optional: Source of diff, for use when merging.
     *
     * This should not need to be set manually.
     */
    source?: ChunkSource;
}
/**
 * Diff representing an added sequence of list entries, or an added substring
 */
export interface IDiffAddRange extends IDiffEntryBase {
    op: 'addrange';
    key: number;
    /**
     * The sequence of values that were added
     */
    valuelist: string | any[];
}
/**
 * Diff representing an added object entry
 */
export interface IDiffAdd extends IDiffEntryBase {
    op: 'add';
    key: string;
    /**
     * The value that was added
     */
    value: any;
}
/**
 * Diff representing a removed object entry
 */
export interface IDiffRemove extends IDiffEntryBase {
    op: 'remove';
    key: string;
}
/**
 * Diff representing a replaced object entry
 */
export interface IDiffReplace extends IDiffEntryBase {
    op: 'replace';
    key: string;
    /**
     * The new value
     */
    value: any;
}
/**
 * Diff representing a removed sequence of list entries, or a removed substring
 */
export interface IDiffRemoveRange extends IDiffEntryBase {
    op: 'removerange';
    key: number;
    /**
     * The length of the sequence that was deleted
     */
    length: number;
}
/**
 * Diff representing a patched entry (object entry or list entry)
 */
export interface IDiffPatch extends IDiffEntryBase {
    op: 'patch';
    /**
     * The collection of sub-diffs describing the patch of the object
     */
    diff: IDiffEntry[] | null;
}
export interface IDiffPatchArray extends IDiffPatch {
    key: number;
}
export interface IDiffPatchObject extends IDiffPatch {
    key: string;
}
/**
 * Describes a diff entry of a single JSON value (object, list, string)
 */
export declare type IDiffEntry = IDiffAddRange | IDiffRemoveRange | IDiffPatch | IDiffAdd | IDiffRemove | IDiffReplace;
export declare type IDiffArrayEntry = IDiffAddRange | IDiffRemoveRange | IDiffPatchArray;
export declare type IDiffObjectEntry = IDiffPatchObject | IDiffAdd | IDiffRemove | IDiffReplace;
export declare type IDiffImmutableArrayEntry = IDiffAddRange | IDiffRemoveRange;
export declare type IDiffImmutableObjectEntry = IDiffAdd | IDiffRemove | IDiffReplace;
export declare type DiffCollection = (IDiffEntry[] | null)[];
/** Create a replacement diff entry */
export declare function opReplace(key: string, value: any): IDiffReplace;
/** Create an addition diff entry */
export declare function opAdd(key: string, value: any): IDiffAdd;
/** Create a removal diff entry */
export declare function opRemove(key: string): IDiffRemove;
/** Create a removal diff entry */
export declare function opAddRange(key: number, valuelist: string | any[]): IDiffAddRange;
/** Create a range removal diff entry */
export declare function opRemoveRange(key: number, length: number): IDiffRemoveRange;
/** Create a range removal diff entry */
export declare function opPatch(key: string | number, diff: IDiffEntry[] | null): IDiffPatch;
/**
 * Validate that a diff operation is valid to apply on a given base sequence
 */
export declare function validateSequenceOp(base: ReadonlyArray<any> | string, entry: IDiffEntry): void;
/**
 * Validate that a diff operation is valid to apply on a given base object
 */
export declare function validateObjectOp(base: any, entry: IDiffEntry, keys: string[]): void;
//# sourceMappingURL=diffentries.d.ts.map