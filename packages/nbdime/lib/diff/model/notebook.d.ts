import * as nbformat from '@jupyterlab/nbformat';
import { IDiffEntry } from '../diffentries';
import { IStringDiffModel } from './string';
import { CellDiffModel } from './cell';
/**
 * Diff model for a Jupyter Notebook
 */
export declare class NotebookDiffModel {
    /**
     * Create a new NotebookDiffModel from a base notebook and a list of diffs.
     *
     * The base as well as the diff entries are normally supplied by the nbdime
     * server.
     */
    constructor(base: nbformat.INotebookContent, diff: IDiffEntry[]);
    /**
     * Diff model of the notebook's root metadata field
     */
    metadata: IStringDiffModel | null;
    /**
     * The default MIME type according to the notebook's root metadata
     */
    mimetype: string;
    /**
     * List of all cell diff models, including unchanged, added/removed and
     * changed cells, in order.
     */
    cells: CellDiffModel[];
    /**
     * List of chunks of cells, e.g. so that any changes that occur in the same
     * location optionally can be shown side by side.
     */
    chunkedCells: CellDiffModel[][];
}
//# sourceMappingURL=notebook.d.ts.map