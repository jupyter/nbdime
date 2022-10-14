import { IDiffEntry } from '../../diff/diffentries';
import { DiffRangePos } from '../../diff/range';
import { StringDiffModel, IStringDiffModel } from '../../diff/model';
import { MergeDecision } from '../../merge/decisions';
import { Chunk } from '../../chunking';
import { DeepCopyableObject } from '../../common/util';
/**
 * A string diff model based on merge decisions.
 */
export declare class DecisionStringDiffModel extends StringDiffModel {
    constructor(base: any, decisions: MergeDecision[], sourceModels: (IStringDiffModel | null)[], collapsible?: boolean, header?: string, collapsed?: boolean);
    decisions: MergeDecision[];
    rawBase: any;
    get additions(): DiffRangePos[];
    set additions(value: DiffRangePos[]);
    get deletions(): DiffRangePos[];
    set deletions(value: DiffRangePos[]);
    get remote(): string;
    set remote(value: string);
    invalidate(): void;
    get invalid(): boolean;
    /**
     * Chunk additions/deletions into line-based chunks, while also producing
     * chunks from source models where the decision is a no-op (action 'base').
     */
    getLineChunks(): Chunk[];
    protected _update(): void;
    protected _additions: DiffRangePos[];
    protected _deletions: DiffRangePos[];
    protected _remote: string;
    protected _outdated: boolean;
    protected _sourceModels: (IStringDiffModel | null)[];
}
/**
 * Abstract base class for a merge model of objects of the type ObjectType,
 * which uses DiffModelType to model each side internally.
 *
 * Implementors need to define the abstract functions createDiffModel and
 * createMergedDiffModel.
 */
export declare abstract class ObjectMergeModel<ObjectType extends DeepCopyableObject, DiffModelType> {
    /**
     * Create a diff model of the correct type given the diff (which might be
     * null)
     */
    protected abstract createDiffModel(diff: IDiffEntry[] | null): DiffModelType;
    /**
     * Create a diff model of the correct type for the merge
     */
    protected abstract createMergedDiffModel(): DiffModelType;
    /**
     *
     */
    constructor(base: ObjectType | null, decisions: MergeDecision[], mimetype: string, whitelist?: string[]);
    /**
     * Base value of the object
     */
    base: ObjectType | null;
    /**
     * The mimetype to use for the source
     */
    mimetype: string;
    /**
     * The merge decisions that apply to this object
     */
    readonly decisions: MergeDecision[];
    /**
     * Apply merge decisions to create the merged cell
     */
    serialize(): ObjectType | null;
    /**
     * Model of the local diff vs. base
     */
    get local(): DiffModelType | null;
    /**
     * Model of the remote diff vs. base
     */
    get remote(): DiffModelType | null;
    /**
     * Model of the diff of the merged cell vs. base
     */
    get merged(): DiffModelType;
    /**
     *
     */
    get subModels(): [DiffModelType | null, DiffModelType | null, DiffModelType];
    /**
     * Prevent further changes to decisions, and label the diffs
     *
     * The labels are used for picking of decisions
     */
    protected _finalizeDecisions(): void;
    /**
     * List of fields to handle
     */
    protected _whitelist: string[] | null;
    protected _local?: DiffModelType | null;
    protected _remote?: DiffModelType | null;
    protected _merged?: DiffModelType;
    protected _finalized: boolean;
}
//# sourceMappingURL=common.d.ts.map