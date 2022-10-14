import { Panel, Widget } from '@lumino/widgets';
import { ISignal } from '@lumino/signaling';
import { FriendlyDragDrop, DragDropPanel } from '../../common/dragpanel';
import { CellMergeWidget } from './cell';
export declare class CellsDragDrop extends FriendlyDragDrop {
    /**
     *
     */
    constructor(options?: DragDropPanel.IOptions);
    /**
     * Called when something has been dropped in the panel.
     *
     * As only internal moves are supported, we know the type of the keys
     */
    protected move(from: number[], to: number[]): void;
    get moved(): ISignal<this, CellsDragDrop.IMovedArgs>;
    private _moved;
}
export declare namespace CellsDragDrop {
    interface IMovedArgs {
        widget: CellMergeWidget;
        oldParent: CellsDragDrop;
        before: CellMergeWidget | null;
        after: CellMergeWidget | null;
    }
}
export declare class ChunkedCellsWidget extends Panel {
    /**
     *
     */
    constructor();
    onResolve(event?: MouseEvent): void;
    dispose(): void;
    header: Widget;
    cells: CellsDragDrop;
    get resolved(): ISignal<this, void>;
    private _resolved;
}
//# sourceMappingURL=dragdrop.d.ts.map