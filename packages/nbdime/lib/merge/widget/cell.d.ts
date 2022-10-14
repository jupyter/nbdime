import * as nbformat from '@jupyterlab/nbformat';
import { Panel, Widget } from '@lumino/widgets';
import { IRenderMimeRegistry } from '@jupyterlab/rendermime';
import { IDiffModel, OutputDiffModel } from '../../diff/model';
import { CellMergeModel } from '../model';
import { RenderableOutputsMergeView } from './output';
export declare const CELLMERGE_CLASS = "jp-Cell-merge";
/**
 * CellMergeWidget for cell changes
 */
export declare class CellMergeWidget extends Panel {
    static createMergeView(local: IDiffModel | null, remote: IDiffModel | null, merged: IDiffModel, editorClasses: string[], readOnly?: boolean): Widget | null;
    protected static getOutputs(models: OutputDiffModel[], base?: boolean): nbformat.IOutput[];
    /**
     *
     */
    constructor(model: CellMergeModel, rendermime: IRenderMimeRegistry, mimetype: string);
    validateMerged(candidate: nbformat.ICell): nbformat.ICell;
    protected init(): void;
    protected createHeader(): void;
    private _createClearOutputToggle;
    private _createDeleteToggle;
    mimetype: string;
    header: Panel;
    headerTitleWidget: Widget;
    sourceView: Widget | null;
    metadataView: Widget | null;
    outputViews: RenderableOutputsMergeView | null;
    set headerTitle(value: string);
    /**
     * Get the model for the widget.
     *
     * #### Notes
     * This is a read-only property.
     */
    get model(): CellMergeModel;
    private _model;
    private _rendermime;
}
//# sourceMappingURL=cell.d.ts.map