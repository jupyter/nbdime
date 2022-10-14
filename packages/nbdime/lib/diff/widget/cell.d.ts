import { Panel } from '@lumino/widgets';
import { IRenderMimeRegistry } from '@jupyterlab/rendermime';
import { CellDiffModel, IDiffModel, ImmutableDiffModel } from '../model';
export declare const CELLDIFF_CLASS = "jp-Cell-diff";
export declare const OUTPUTS_DIFF_CLASS = "jp-Diff-outputsContainer";
/**
 * CellDiffWidget for cell changes
 */
export declare class CellDiffWidget extends Panel {
    /**
     *
     */
    constructor(model: CellDiffModel, rendermime: IRenderMimeRegistry, mimetype: string);
    protected init(): void;
    static createPrompts(model: ImmutableDiffModel, parent: CellDiffModel): Panel;
    /**
     * Create a new sub-view.
     */
    static createView(model: IDiffModel, parent: CellDiffModel, editorClasses: string[], rendermime: IRenderMimeRegistry): Panel;
    mimetype: string;
    /**
     * Get the model for the widget.
     *
     * #### Notes
     * This is a read-only property.
     */
    get model(): CellDiffModel;
    protected _model: CellDiffModel;
    protected _rendermime: IRenderMimeRegistry;
}
//# sourceMappingURL=cell.d.ts.map