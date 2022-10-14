import * as nbformat from '@jupyterlab/nbformat';
import { IRenderMimeRegistry, IOutputModel } from '@jupyterlab/rendermime';
import { OutputArea, OutputAreaModel, IOutputAreaModel } from '@jupyterlab/outputarea';
import { DropAction, IDragEvent } from '@lumino/dragdrop';
import { PanelLayout } from '@lumino/widgets';
import { DragDropPanel } from '../../common/dragpanel';
/**
 * An OutputAreaModel which allows for reordering of its
 * outputs.
 */
export declare class ReorderableOutputModel extends OutputAreaModel {
    insert(index: number, item: IOutputModel): void;
    move(fromIndex: number, toIndex: number): void;
    remove(index: number): IOutputModel | undefined;
}
/**
 * An OutputArea which supports the reordering
 * capabilities of ReorderableOutputModel
 */
export declare class ReorderableOutputWidget extends OutputArea {
    readonly model: ReorderableOutputModel;
    /**
     * Follow changes on the model state.
     */
    protected onModelChanged(sender: IOutputAreaModel, args: IOutputAreaModel.ChangedArgs): void;
}
/**
 * Widget for showing side by side comparison and picking of merge outputs
 */
export declare class RenderableOutputsMergeView extends DragDropPanel {
    static makeOutputsDraggable(area: OutputArea): void;
    private static get deleteDrop();
    private static _deleteDrop;
    /**
     *
     */
    constructor(merged: nbformat.IOutput[], classes: string[], rendermime: IRenderMimeRegistry, base: nbformat.IOutput[] | null, remote: nbformat.IOutput[] | null, local: nbformat.IOutput[] | null);
    init(classes: string[]): void;
    /**
     * Overrided version to allow drag and drop from source lists to merged list
     */
    protected findDragTarget(handle: HTMLElement): HTMLElement | null;
    protected getIndexOfChildNode(node: HTMLElement, parent?: PanelLayout): any;
    /**
     * Called when something has been dropped in the panel.
     *
     * As only internal moves are supported, we know the type of the keys
     */
    protected move(from: number[], to: number[]): void;
    /**
     * Find a drop target from a given node
     *
     * Returns null if no valid drop target was found.
     */
    protected findDropTarget(node: HTMLElement): HTMLElement | null;
    protected processDrop(dropTarget: HTMLElement, event: IDragEvent): void;
    protected getDragImage(handle: HTMLElement): HTMLElement | null;
    protected startDrag(handle: HTMLElement, clientX: number, clientY: number): void;
    protected onDragComplete(action: DropAction): void;
    base: OutputAreaModel | null;
    remote: OutputAreaModel | null;
    local: OutputAreaModel | null;
    merged: ReorderableOutputModel;
    mergePane: ReorderableOutputWidget;
    panes: OutputArea[];
    rendermime: IRenderMimeRegistry;
}
//# sourceMappingURL=output.d.ts.map