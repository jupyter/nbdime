import { IDiffEntry, DiffCollection } from '../diff/diffentries';
export declare type DecisionPath = (string | number)[];
export interface IMergeDecision {
    local_diff?: IDiffEntry[] | null;
    remote_diff?: IDiffEntry[] | null;
    conflict?: boolean;
    action?: string;
    common_path?: DecisionPath;
    custom_diff?: IDiffEntry[] | null;
    similar_insert?: IDiffEntry[] | null;
}
export declare type Action = 'base' | 'local' | 'remote' | 'local_then_remote' | 'remote_then_local' | 'custom' | 'clear' | 'clear_parent' | 'either';
export declare class MergeDecision {
    /**
     * Create a MergeDecision from JSON structure.
     *
     * If any of the JSON fields are undefined, the values
     * will be set to default values. The default values
     * of all values except the common path can be overridden
     * by the additional parameters to this function.
     */
    constructor(decision: IMergeDecision, localDiff?: IDiffEntry[] | null, remoteDiff?: IDiffEntry[] | null, action?: Action, conflict?: boolean, customDiff?: IDiffEntry[] | null, similarInsert?: IDiffEntry[] | null);
    /**
     * Create a MergeDecision from values.
     *
     * Default values are used for any missing parameters.
     */
    constructor(commonPath: DecisionPath, localDiff?: IDiffEntry[] | null, remoteDiff?: IDiffEntry[] | null, action?: Action, conflict?: boolean, customDiff?: IDiffEntry[] | null, similarInsert?: IDiffEntry[] | null);
    /**
     * MergeDecision copy constructor.
     */
    constructor(decision: MergeDecision);
    setValuesFrom(other: MergeDecision): void;
    get localPath(): DecisionPath;
    get absolutePath(): DecisionPath;
    set absolutePath(value: DecisionPath);
    action: Action;
    localDiff: IDiffEntry[] | null;
    remoteDiff: IDiffEntry[] | null;
    customDiff: IDiffEntry[] | null;
    similarInsert: IDiffEntry[] | null;
    conflict: boolean;
    protected _path: DecisionPath;
    pushPath(key: number | string): void;
    get diffs(): DiffCollection;
    set diffs(value: DiffCollection);
    serialize(): IMergeDecision;
    level: number;
}
/**
 * Compare to DecisionPath's for sorting.
 *
 * The rules are that deeper paths sort before other paths
 * with the same prefix, as they correspond to patch ops,
 * which will not affect the indexing of following decisions
 * on lists.
 *
 * @param {DecisionPath} a The first decision path
 * @param {DecisionPath} b The second decision path
 * @returns {number} Returns a negative number if a should
 *  sort first, positive number if b should sort first, or
 *  zero if the are identical.
 */
export declare function decisionPathSortKey(a: DecisionPath, b: DecisionPath): number;
/**
 * Compare the paths of two decisions for sorting.
 *
 * This is a thin wrapper around decisionPathSortKey
 *
 * @export
 * @param {MergeDecision} a The first decision
 * @param {MergeDecision} b The second decision
 * @returns {number}  Returns a negative number if a should
 *  sort first, positive number if b should sort first, or
 *  zero if the are identical.
 */
export declare function decisionSortKey(a: MergeDecision, b: MergeDecision): number;
/**
 * Adds a decision to an existing, sorted collection of merge decisions
 *
 * Ensures that the location of the newly added decision
 * will comply with the format specification
 *
 * @export
 * @param {MergeDecision[]} decisions
 * @param {MergeDecision} toAdd
 * @param {(number | string)} [firstKey]
 * @returns {void}
 */
export declare function addSorted(decisions: MergeDecision[], toAdd: MergeDecision, firstKey?: number | string): void;
export declare function popPath(diffs: DiffCollection, popInner?: boolean): {
    diffs: DiffCollection;
    key: string | number;
} | null;
export declare function pushPath(diffs: IDiffEntry[], prefix: DecisionPath): IDiffEntry[];
/**
 * Expand the `common_path` field of the merge decisions for optimized
 * processing. Modifies the merge decisions in-place.
 */
export declare function resolveCommonPaths(decisions: MergeDecision[]): void;
/**
 * Apply a merge decision's action to a base.
 *
 * Returns a new, patched object, leaving the base unmodified.
 */
export declare function applyDecisions<T>(base: T, decisions: MergeDecision[]): T;
/**
 * Builds a diff for direct application on base. The `which` argument either
 * selects the 'local', 'remote' or 'merged' diffs.
 */
export declare function buildDiffs(base: any, decisions: MergeDecision[], which: 'local' | 'remote' | 'merged'): IDiffEntry[] | null;
/**
 * Move a path prefix in a merge decision from `common_path` to the diffs.
 *
 * This is done by wrapping the diffs in nested patch ops.
 */
export declare function pushPatchDecision(decision: MergeDecision, prefix: DecisionPath): MergeDecision;
/**
 * Filter decisions based on matching (segment of) path
 *
 * Checks whether each decision's path start with `path`. If `skipLevels` is
 * given, the first levels of the decision's path is ignored for the comparison.
 *
 * Once matched, the matching decisions' levels are adjusted such that they
 * point to after the matching segment.
 *
 * Example:
 * Given a list of decisions with paths:
 *   /cells/0/outputs/0
 *   /cells/0/outputs/1
 *   /cells/2/outputs/1
 *   /cells/12/outputs/0/data
 *
 * If called with path `['cells']`:
 *   All decisions will be returned, with level set to 1
 * If called with path `['cells', 0]`:
 *   The first two will be returned, with level set to 2
 * If called with path `['outputs']`, and skipLevel = 2:
 *   All decisions will be returned, with level set to 3
 * If called with path `['outputs', 0]`, and skipLevel = 2:
 *   Decision 1 and 4 will be returned, with level set to 4
 *
 * Note that since the same decision instances are returned, this will modify
 * the level of the passed decisions.
 */
export declare function filterDecisions(decisions: MergeDecision[], path: DecisionPath, skipLevels?: number, maxLength?: number): MergeDecision[];
//# sourceMappingURL=decisions.d.ts.map