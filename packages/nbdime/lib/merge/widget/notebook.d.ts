import * as nbformat from '@jupyterlab/nbformat';
import { IRenderMimeRegistry } from '@jupyterlab/rendermime';
import { Panel } from '@lumino/widgets';
import { NotebookMergeModel } from '../model';
import { MetadataMergeWidget } from './metadata';
import { CellMergeWidget } from './cell';
import { CellsDragDrop, ChunkedCellsWidget } from './dragdrop';
/**
 * NotebookMergeWidget
 */
export declare class NotebookMergeWidget extends Panel {
    constructor(model: NotebookMergeModel, rendermime: IRenderMimeRegistry);
    /**
     * Start adding sub-widgets.
     *
     * Separated from constructor to allow 'live' adding of widgets
     */
    init(): Promise<void>;
    validateMerged(candidate: nbformat.INotebookContent): nbformat.INotebookContent;
    /**
     * Get the model for the widget.
     *
     * #### Notes
     * This is a read-only property.
     */
    get model(): NotebookMergeModel;
    protected onDragDropMove(sender: CellsDragDrop, args: CellsDragDrop.IMovedArgs): void;
    protected onChunkResolved(sender: ChunkedCellsWidget, args: void): void;
    protected metadataWidget: MetadataMergeWidget | null;
    protected cellWidgets: CellMergeWidget[];
    protected cellContainer: CellsDragDrop;
    private _model;
    private _rendermime;
}
//# sourceMappingURL=notebook.d.ts.map