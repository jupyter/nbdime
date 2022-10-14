export interface DeepCopyableObject {
    [key: string]: any | undefined;
    prototype?: DeepCopyableObject;
}
export declare type DeepCopyableValue = DeepCopyableObject | DeepCopyableObject[] | string | number | boolean | null;
/**
 * Check whether a value is in an array.
 */
export declare function valueIn(value: any, array: Array<any>): boolean;
/**
 * Check whether array is null or empty, and type guards agains null
 */
export declare function hasEntries<T>(array: T[] | null): array is T[];
/**
 * Splits a multinline string into an array of lines
 *
 * @export
 * @param {string} multiline
 * @returns {string[]}
 */
export declare function splitLines(multiline: string): string[];
/**
 * Deepcopy routine for JSON-able data types
 */
export declare function deepCopy(obj: null): null;
export declare function deepCopy<T extends DeepCopyableValue>(obj: T): T;
export declare function deepCopy<T extends DeepCopyableValue>(obj: T | null): T | null;
/**
 * Shallow copy routine for objects
 */
export declare function shallowCopy<T extends {
    [key: string]: any;
}>(original: T): T;
/**
 * Do a shallow, element-wise equality comparison on two arrays.
 */
export declare function arraysEqual(a: any[] | null, b: any[] | null): boolean;
/**
 * Find the shared common starting sequence in two arrays
 */
export declare function findSharedPrefix(a: any[] | null, b: any[] | null): any[] | null;
/**
 * Check whether `parent` is contained within the start of `child`
 *
 * Note on terminology: Parent is here the shortest array, as it will
 * be the parent in a tree-view of values, e.g. a path. In other words, parent
 * is a subsequence of child.
 */
export declare function isPrefixArray(parent: any[] | null, child: any[] | null): boolean;
/**
 * Sort array by attribute `key` (i.e. compare by array[0][key] < array[1][key]). Stable.
 */
export declare function sortByKey<T extends {
    [key: string]: any;
}>(array: T[], key: string): T[];
/**
 * Utility function to repeat a string
 */
export declare function repeatString(str: string, count: number): string;
/**
 * Calculate the cumulative sum of string lengths for an array of strings
 *
 * Example:
 *   For the arary ['ab', '123', 'y', '\t\nfoo'], the output would be
 *   [2, 5, 6, 11]
 */
export declare function accumulateLengths(arr: string[]): number[];
/**
 * Filter for Array.filter to only have unique values
 */
export declare function unique<T>(value: T, index: number, self: T[]): boolean;
/**
 * Return the intersection of two arrays (with no duplicates)
 */
export declare function intersection<T>(a: T[], b: T[]): T[];
/**
 * Similar to Array.sort, but guaranteed to keep order stable
 * when compare function returns 0
 */
export declare function stableSort<T>(arr: T[], compare: (a: T, b: T) => number): T[];
/**
 * Copy an object, possibly extending it in the process
 */
export declare function copyObj<T extends {
    [key: string]: any;
}>(obj: T): T;
export declare function copyObj<T extends {
    [key: string]: any;
}, U extends {
    [key: string]: any;
}>(obj: T, target?: U): T & U;
/**
 * Create or populate a select element with string options
 */
export declare function buildSelect(options: string[], select?: HTMLSelectElement): HTMLSelectElement;
//# sourceMappingURL=util.d.ts.map