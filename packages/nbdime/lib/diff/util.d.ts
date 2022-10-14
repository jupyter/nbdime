import { IDiffEntry, IDiffArrayEntry } from './diffentries';
/**
 * The indentation to use for JSON stringify.
 */
export declare const JSON_INDENT = "  ";
/**
 * Search the list of diffs for an entry with the given key.
 *
 * Returns the first found entry, or null if not entry was found.
 */
export declare function getSubDiffByKey(diff: IDiffEntry[] | null, key: string | number): IDiffEntry[] | null;
/**
 * Search the list of diffs for an entry with the given key.
 *
 * Returns the first found entry, or null if not entry was found.
 */
export declare function getDiffEntryByKey(diff: IDiffEntry[] | null, key: string | number): IDiffEntry | null;
/**
 * Remove the merge source indicator from a diff (returns a copy).
 */
export declare function stripSource(diff: IDiffEntry[] | null): IDiffEntry[] | null;
/**
 * Translates a diff of strings split by str.splitlines() to a diff of the
 * joined multiline string
 */
export declare function flattenStringDiff(val: string[] | string, diff: IDiffArrayEntry[]): IDiffArrayEntry[];
//# sourceMappingURL=util.d.ts.map