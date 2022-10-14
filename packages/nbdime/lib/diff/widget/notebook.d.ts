import { Panel } from '@lumino/widgets';
import { IRenderMimeRegistry } from '@jupyterlab/rendermime';
import { NotebookDiffModel } from '../model';
/**
 * NotebookDiffWidget
 */
export declare class NotebookDiffWidget extends Panel {
    constructor(model: NotebookDiffModel, rendermime: IRenderMimeRegistry);
    /**
     * Start adding sub-widgets.
     *
     * Separated from constructor to allow 'live' adding of widgets
     */
    init(): Promise<void>;
    /**
     * Get the model for the widget.
     *
     * #### Notes
     * This is a read-only property.
     */
    get model(): NotebookDiffModel;
    private _model;
    private _rendermime;
    private addMetadata(): void;
    private addChunks(): void;
    private addCellDiffWidget(cellDiffModel): CellDiffWidget;
    addChunkPanel(cellDiffModel): void;
}
//# sourceMappingURL=notebook.d.ts.map
