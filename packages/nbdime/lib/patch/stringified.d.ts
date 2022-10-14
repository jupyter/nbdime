import { ReadonlyJSONValue } from '@lumino/coreutils';
import { IDiffEntry, IDiffArrayEntry } from '../diff/diffentries';
import { DiffRangeRaw } from '../diff/range';
declare global {
    interface ArrayConstructor {
        isArray(arg: ReadonlyArray<any> | any): arg is ReadonlyArray<any>;
    }
}
/**
 * The result of a patch operation of a stringified object.
 *
 * Contains the resulting remote string, as well as ranges describing which
 * parts of the string were changed.
 */
export declare type StringifiedPatchResult = {
    /**
     * The patched string value
     */
    remote: string;
    /**
     * Position ranges indicating added content, as indices into the remote value
     */
    additions: DiffRangeRaw[];
    /**
     * Position ranges indicating removed content, as indices into the base value
     */
    deletions: DiffRangeRaw[];
};
/**
 * Ordered stringify. Wraps stableStringify(), but handles indentation.
 *
 * indentFirst controls whether the first line is indented as well, and
 * defaults to true.
 */
export declare function stringify(values: ReadonlyJSONValue | null, level?: number, indentFirst?: boolean): string;
/**
 * Ensure value is string, if not stringify.
 */
export declare function stringifyAndBlankNull(value: ReadonlyJSONValue | null): string;
/**
 * Patch a stringified JSON object.
 *
 * Returns the stringified value of the patched JSON object, as well as
 * position ranges indicating which parts of the string that was added or
 * removed.
 *
 * Internally, this builds the ranges based on the actual supplied diff, which
 * can therefore differ from a straigh string-based diff of stringified JSON
 * objects.
 */
export declare function patchStringified(base: ReadonlyJSONValue, diff: IDiffEntry[] | null, level?: number): StringifiedPatchResult;
/**
 * Patch a string according to a line based diff
 */
export declare function patchString(base: string, diff: IDiffArrayEntry[] | null, level: number, stringifyPatch?: boolean): StringifiedPatchResult;
//# sourceMappingURL=stringified.d.ts.map