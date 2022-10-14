import { IDiffModel } from './common';
import { IDiffImmutableObjectEntry } from '../diffentries';
export declare type ImmutableValue = number | boolean | null;
/**
 * Standard implementation of the IStringDiffModel interface.
 */
export declare class ImmutableDiffModel implements IDiffModel {
    /**
     * ImmutableDiffModel constructor.
     *
     * `collapsible` and `collapsed` both defaults to false.
     */
    constructor(base: ImmutableValue | undefined, remote: ImmutableValue | undefined, collapsible?: boolean, header?: string, collapsed?: boolean);
    get unchanged(): boolean;
    get added(): boolean;
    get deleted(): boolean;
    base: ImmutableValue | undefined;
    remote: ImmutableValue | undefined;
    collapsible: boolean;
    collapsibleHeader: string;
    startCollapsed: boolean;
}
/**
 * Create an ImmutableDiffModel from a base value, a remote value, and a single diff entry.
 *
 * Note: The requirement of a single diff entry means it will not support
 * an add/replace pair on the same key, as this should instead be represented
 * by a 'replace' op.
 *
 * @export
 * @param {(ImmutableValue | undefined)} base : The base value
 * @param {(IDiffImmutableObjectEntry | null)} diff : The diff entry, or null if unchanged
 * @returns {ImmutableDiffModel}
 */
export declare function createImmutableModel(base: ImmutableValue | undefined, remote: ImmutableValue | undefined, diff?: IDiffImmutableObjectEntry | null): ImmutableDiffModel;
//# sourceMappingURL=immutable.d.ts.map