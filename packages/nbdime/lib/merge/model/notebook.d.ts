import * as nbformat from '@jupyterlab/nbformat';
import { IMergeDecision, MergeDecision } from '../../merge/decisions';
import { CellMergeModel } from './cell';
import { MetadataMergeModel } from './metadata';
/**
 * Diff model for a Jupyter Notebook
 */
export declare class NotebookMergeModel {
    static preprocessDecisions(rawMergeDecisions: IMergeDecision[]): MergeDecision[];
    /**
     * Create a new NotebookMergeModel from a base notebook and a list of
     * merge decisions.
     *
     * The base as well as the merge decisions are normally supplied by the
     * nbdime server.
     */
    constructor(base: nbformat.INotebookContent, rawMergeDecisions: IMergeDecision[]);
    serialize(): nbformat.INotebookContent;
    get decisions(): MergeDecision[];
    get conflicts(): MergeDecision[];
    /**
     * Base notebook of the merge
     */
    base: nbformat.INotebookContent;
    /**
     * List of individual cell merges
     */
    cells: CellMergeModel[];
    /**
     * Metadata merge model
     */
    metadata: MetadataMergeModel;
    /**
     * The default MIME type according to the notebook's root metadata
     */
    mimetype: string;
    /**
     * Whether there are unsaved changes
     */
    unsavedChanges: boolean;
    /**
     * Correlate the different cells in the diff lists into a merge list
     */
    protected buildCellList(decisions: MergeDecision[]): CellMergeModel[];
}
//# sourceMappingURL=notebook.d.ts.map