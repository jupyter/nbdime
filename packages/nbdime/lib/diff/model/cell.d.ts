import * as nbformat from '@jupyterlab/nbformat';
import { IDiffEntry } from '../diffentries';
import { IStringDiffModel } from './string';
import { OutputDiffModel } from './output';
import { ImmutableDiffModel } from './immutable';
/**
 * Diff model for individual Notebook Cells
 */
export declare class CellDiffModel {
    constructor(source: IStringDiffModel, metadata: IStringDiffModel, outputs: OutputDiffModel[] | null, executionCount: ImmutableDiffModel | null, cellType: string);
    /**
     * Diff model for the source field.
     */
    source: IStringDiffModel;
    /**
     * Diff model for the metadata field.
     */
    metadata: IStringDiffModel;
    /**
     * Diff model for the outputs field. Can be null.
     *
     * A null value signifies that the cell is not a
     * code cell type.
     */
    outputs: OutputDiffModel[] | null;
    /**
     * Diff model for the execution_count field. Can be null.
     *
     * A null value signifies that the cell is not a
     * code cell type.
     */
    executionCount: ImmutableDiffModel | null;
    /**
     * The type of the notebook cell
     */
    cellType: string;
    /**
     * Whether the cell has remained unchanged
     */
    get unchanged(): boolean;
    /**
     * Whether the cell has been added to the notebook (new cell)
     */
    get added(): boolean;
    /**
     * Whether the cell has been deleted/removed from the notebook
     */
    get deleted(): boolean;
    /**
     * Chunked outputs
     */
    getChunkedOutputs(): OutputDiffModel[][] | null;
}
export declare function createPatchedCellDiffModel(base: nbformat.ICell, diff: IDiffEntry[] | null, nbMimetype: string): CellDiffModel;
export declare function createUnchangedCellDiffModel(base: nbformat.ICell, nbMimetype: string): CellDiffModel;
export declare function createAddedCellDiffModel(remote: nbformat.ICell, nbMimetype: string): CellDiffModel;
export declare function createDeletedCellDiffModel(base: nbformat.ICell, nbMimetype: string): CellDiffModel;
//# sourceMappingURL=cell.d.ts.map