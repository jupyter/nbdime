import { ReadonlyJSONObject } from '@lumino/coreutils';
import { IIterator } from '@lumino/algorithm';
import { IDiffObjectEntry } from '../diff/diffentries';
export declare class PatchObjectHelper implements IIterator<string> {
    constructor(base: ReadonlyJSONObject, diff: IDiffObjectEntry[] | null);
    isDiffKey(key: string): boolean;
    getDiffEntry(key: string): IDiffObjectEntry;
    /**
     * Whether there any dict entries after the current add/remove diff op.
     *
     * Note that if the current op is a remove op, it does not take into
     * account any entries added below it. Similarly, if the current op is
     * an add op it does not take into account any entries that are
     * removed after it.
     *
     * Assumes current key is a diff key to either an add or remove op.
     * @returns {boolean}
     */
    entriesAfterCurrentAddRem(): boolean;
    iter(): IIterator<string>;
    keys(): IIterator<string>;
    next(): string | undefined;
    clone(): IIterator<string>;
    baseKeys: string[];
    private _currentIsAddition;
    private _diffKeys;
    private _diffLUT;
    private _remainingKeys;
}
//# sourceMappingURL=common.d.ts.map