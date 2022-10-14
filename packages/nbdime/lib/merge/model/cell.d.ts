import * as nbformat from '@jupyterlab/nbformat';
import { Signal } from '@lumino/signaling';
import { IDiffEntry, IDiffPatchObject } from '../../diff/diffentries';
import { CellDiffModel } from '../../diff/model';
import { MergeDecision } from '../../merge/decisions';
import { ObjectMergeModel } from './common';
/**
 * CellMergeModel
 */
export declare class CellMergeModel extends ObjectMergeModel<nbformat.ICell, CellDiffModel> {
    constructor(base: nbformat.ICell | null, decisions: MergeDecision[], mimetype: string);
    /**
     * Whether the cell is present in only one of the two side (local/remote)
     */
    onesided: boolean;
    /**
     * Run time flag whether the user wants to delete the cell
     *
     * @type {boolean}
     */
    get deleteCell(): boolean;
    set deleteCell(value: boolean);
    private _deleteCell;
    readonly deleteCellChanged: Signal<CellMergeModel, boolean>;
    /**
     * Run time flag whether the user wants to clear the outputs of the cell
     *
     * @type {boolean}
     */
    get clearOutputs(): boolean;
    set clearOutputs(value: boolean);
    private _clearOutputs;
    readonly clearOutputsChanged: Signal<CellMergeModel, boolean>;
    /**
     * Whether source is the same in local and remote
     */
    get agreedSource(): boolean;
    /**
     * Whether metadata is the same in local and remote
     */
    get agreedMetadata(): boolean;
    /**
     * Whether outputs are the same in local and remote
     */
    get agreedOutputs(): boolean;
    /**
     * Whether cell is the same in local and remote
     */
    get agreedCell(): boolean;
    /**
     * Whether the cell has any conflicted decisions.
     */
    get conflicted(): boolean;
    /**
     * Whether the cell has any conflicted decisions on a specific key.
     */
    hasConflictsOn(key: string): boolean;
    /**
     * Whether the cell has any conflicted decisions on source.
     */
    get sourceConflicted(): boolean;
    /**
     * Whether the cell has any conflicted decisions on metadata.
     */
    get metadataConflicted(): boolean;
    /**
     * Whether the cell has any conflicted decisions.
     */
    get outputsConflicted(): boolean;
    /**
     * Clear any conflicts on decisions on outputs
     */
    clearOutputConflicts(): void;
    /**
     * Get the decision on `execution_count` field (should only be one).
     *
     * Returns null if no decision on `execution_count` was found.
     */
    getExecutionCountDecision(): MergeDecision | null;
    /**
     * Apply merge decisions to create the merged cell
     */
    serialize(): nbformat.ICell | null;
    protected processDecisions(decisions: MergeDecision[]): void;
    /**
     * Apply a cell level decision to the model
     *
     * This creates the revelant kinds of models
     */
    protected applyCellLevelDecision(md: MergeDecision): MergeDecision[];
    /**
     * Split a decision with a patch on one side into one decision
     * for each sub entry in the patch.
     */
    protected splitPatch(md: MergeDecision, localPatch: IDiffPatchObject | null, remotePatch: IDiffPatchObject | null): MergeDecision[];
    /**
     * Split decisions on 'source' by chunks.
     *
     * This prevents one decision from contributing to more than one chunk.
     */
    protected splitOnSourceChunks(decisions: MergeDecision[]): MergeDecision[];
    protected createDiffModel(diff: IDiffEntry[]): CellDiffModel;
    protected createMergedDiffModel(): CellDiffModel;
}
//# sourceMappingURL=cell.d.ts.map