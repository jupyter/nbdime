import { Panel, PanelLayout, Widget } from '@lumino/widgets';
import { Message } from '@lumino/messaging';
import { MimeData } from '@lumino/coreutils';
import { Drag, IDragEvent, DropAction, SupportedActions } from '@lumino/dragdrop';
/**
 * MIME type representing drag data by index
 */
export declare const MIME_INDEX = "application/vnd.jupyter.dragindex";
/**
 * Determine whether node is equal to or a decendant of our panel, and that is does
 * not belong to a nested drag panel.
 */
export declare function belongsToUs(node: HTMLElement, parentClass: string, parentNode: HTMLElement): boolean;
/**
 * Find the direct child node of `parent`, which has `node` as a descendant.
 * Alternatively, parent can be a collection of children.
 *
 * Returns null if not found.
 */
export declare function findChild(parent: HTMLElement | HTMLElement[], node: HTMLElement): HTMLElement | null;
/**
 * A panel class which allows the user to drop mime data onto it.
 *
 * To complete the class, the following functions need to be implemented:
 *  - processDrop: Process pre-screened drop events
 *
 * The functionallity of the class can be extended by overriding the following
 * functions:
 *  - findDropTarget(): Override if anything other than the direct children
 *    of the widget's node are to be the drop targets.
 *
 * For maximum control, `evtDrop` can be overriden.
 */
export declare abstract class DropPanel extends Panel {
    /**
     * Construct a drop widget.
     */
    constructor(options?: DropPanel.IOptions);
    /**
     * Whether the widget should accept drops from an external source,
     * or only accept drops from itself.
     * Defaults to false, which will disallow all drops unless widget
     * is also a drag widget.
     */
    acceptDropsFromExternalSource: boolean;
    /**
     * Handle the DOM events for the widget.
     *
     * @param event - The DOM event sent to the widget.
     *
     * #### Notes
     * This method implements the DOM `EventListener` interface and is
     * called in response to events on the drop widget's node. It should
     * not be called directly by user code.
     */
    handleEvent(event: Event): void;
    protected validateSource(event: IDragEvent): boolean;
    /**
     * Processes a drop event.
     *
     * This function is called after checking:
     *  - That the `dropTarget` is a valid drop target
     *  - The value of `event.source` if `acceptDropsFromExternalSource` is false
     */
    protected abstract processDrop(dropTarget: HTMLElement, event: IDragEvent): void;
    /**
     * Find a drop target from a given drag event target.
     *
     * Returns null if no valid drop target was found.
     *
     * The default implementation returns the direct child that is the parent of
     * `node`, or `node` if it is itself a direct child. It also checks that the
     * needed mime type is included
     */
    protected findDropTarget(input: HTMLElement, mimeData: MimeData): HTMLElement | null;
    /**
     * Handle the `'p-drop'` event for the widget.
     *
     * Responsible for pre-processing event before calling `processDrop`.
     *
     * Should normally only be overriden if you cannot achive your goal by
     * other overrides.
     */
    protected evtDrop(event: IDragEvent): void;
    /**
     * Handle `after_attach` messages for the widget.
     */
    protected onAfterAttach(msg: Message): void;
    /**
     * Handle `before_detach` messages for the widget.
     */
    protected onBeforeDetach(msg: Message): void;
    /**
     * Handle the `'p-dragenter'` event for the widget.
     */
    private _evtDragEnter;
    /**
     * Handle the `'p-dragleave'` event for the widget.
     */
    private _evtDragLeave;
    /**
     * Handle the `'p-dragover'` event for the widget.
     */
    private _evtDragOver;
    /**
     * Clear existing drop target from out children.
     *
     * #### Notes
     * This function assumes there are only one active drop target
     */
    private _clearDropTarget;
}
/**
 * An internal base class for implementing drag operations on top
 * of drop class.
 */
export declare abstract class DragDropPanelBase extends DropPanel {
    /**
     * Construct a drag and drop base widget.
     */
    constructor(options?: DragDropPanel.IOptions);
    /**
     * Whether all direct children of the widget are handles, or only those
     * designated as handles. Defaults to false.
     */
    childrenAreDragHandles: boolean;
    /**
     * Dispose of the resources held by the directory listing.
     */
    dispose(): void;
    /**
     * Handle the DOM events for the widget.
     *
     * @param event - The DOM event sent to the widget.
     *
     * #### Notes
     * This method implements the DOM `EventListener` interface and is
     * called in response to events on the drag widget's node. It should
     * not be called directly by user code.
     */
    handleEvent(event: Event): void;
    /**
     * Adds mime data represeting the drag data to the drag event's MimeData bundle.
     */
    protected abstract addMimeData(handle: HTMLElement, mimeData: MimeData): void;
    /**
     * Finds the drag target (the node to move) from a drag handle.
     *
     * Returns null if no valid drag target was found.
     *
     * The default implementation returns the direct child that is the ancestor of
     * (or equal to) the handle.
     */
    protected findDragTarget(handle: HTMLElement): HTMLElement | null;
    /**
     * Returns the drag image to use when dragging using the given handle.
     *
     * The default implementation returns a clone of the drag target.
     */
    protected getDragImage(handle: HTMLElement): HTMLElement | null;
    /**
     * Called when a drag has completed with this panel as a source
     */
    protected onDragComplete(action: DropAction): void;
    /**
     * Handle `after_attach` messages for the widget.
     */
    protected onAfterAttach(msg: Message): void;
    /**
     * Handle `before_detach` messages for the widget.
     */
    protected onBeforeDetach(msg: Message): void;
    /**
     * Start a drag event.
     *
     * Called when dragginging and DRAG_THRESHOLD is met.
     *
     * Should normally only be overriden if you cannot achieve your goal by
     * other overrides.
     */
    protected startDrag(handle: HTMLElement, clientX: number, clientY: number): void;
    /**
     * Drag data stored in _startDrag
     */
    protected drag: Drag | null;
    protected dragHandleClass: string;
    /**
     * Check if node, or any of nodes ancestors are a drag handle
     *
     * If it is a drag handle, it returns the handle, if not returns null.
     */
    private _findDragHandle;
    /**
     * Handle the `'mousedown'` event for the widget.
     */
    private _evtDragMousedown;
    /**
     * Handle the `'mouseup'` event for the widget.
     */
    private _evtDragMouseup;
    /**
     * Handle the `'mousemove'` event for the widget.
     */
    private _evtDragMousemove;
    /**
     * Data stored on mouse down to determine if drag treshold has
     * been overcome, and to initialize drag once it has.
     */
    private _clickData;
}
/**
 * A panel which allows the user to initiate drag operations.
 *
 * Any descendant element with the drag handle class `'jp-mod-dragHandle'`
 * will serve as a handle that can be used for dragging. If DragPanels are
 * nested, handles will only belong to the closest parent DragPanel. For
 * convenience, the functions `makeHandle`, `unmakeHandle` and
 * `createDefaultHandle` can be used to indicate which elements should be
 * made handles. `createDefaultHandle` will create a new element as a handle
 * with a default styling class applied. Optionally, `childrenAreDragHandles`
 * can be set to indicate that all direct children are themselve drag handles.
 *
 * To complete the class, the following functions need to be implemented:
 * - addMimeData: Adds mime data to new drag events
 *
 * The functionallity of the class can be extended by overriding the following
 * functions:
 *  - findDragTarget(): Override if anything other than the direct children
 *    of the widget's node are to be drag targets.
 *  - getDragImage: Override to change the drag image (the default is a
 *    copy of the drag target).
 *  - onDragComplete(): Callback on drag source when a drag has completed.
 */
export declare abstract class DragPanel extends DragDropPanelBase {
    /**
     * Construct a drag widget.
     */
    constructor(options?: DragPanel.IOptions);
    /**
     * No-op on DragPanel, as it does not support dropping
     */
    protected processDrop(dropTarget: HTMLElement, event: IDragEvent): void;
    /**
     * Simply returns null for DragPanel, as it does not support dropping
     */
    protected findDropTarget(input: HTMLElement, mimeData: MimeData): HTMLElement | null;
}
/**
 * A widget which allows the user to rearrange widgets in the panel by
 * drag and drop. An internal drag and drop of a widget will cause it
 * to be inserted (by `insertWidget`) in the index of the widget it was
 * dropped on.
 *
 * Any descendant element with the drag handle class `'jp-mod-dragHandle'`
 * will serve as a handle that can be used for dragging. If DragPanels are
 * nested, handles will only belong to the closest parent DragPanel. For
 * convenience, the functions `makeHandle`, `unmakeHandle` and
 * `createDefaultHandle` can be used to indicate which elements should be
 * made handles. `createDefaultHandle` will create a new element as a handle
 * with a default styling class applied. Optionally, `childrenAreDragHandles`
 * can be set to indicate that all direct children are themselve drag handles.
 *
 * The functionallity of the class can be extended by overriding the following
 * functions:
 *  - addMimeData: Override to add other drag data to the mime bundle.
 *    This is often a necessary step for allowing dragging to external
 *    drop targets.
 *  - processDrop: Override if you need to handle other mime data than the
 *    default. For allowing drops from external sources, the field
 *    `acceptDropsFromExternalSource` should be set as well.
 *  - findDragTarget(): Override if anything other than the direct children
 *    of the widget's node are to be drag targets.
 *  - findDropTarget(): Override if anything other than the direct children
 *    of the widget's node are to be the drop targets.
 *  - getIndexOfChildNode(): Override to change the key used to represent
 *    the drag and drop target (default is index of child widget).
 *  - move(): Override to change how a move is handled.
 *  - getDragImage: Override to change the drag image (the default is a
 *    copy of the drag target).
 *  - onDragComplete(): Callback on drag source when a drag has completed.
 *
 * To drag and drop other things than all direct children, the following functions
 * should be overriden: `findDragTarget`, `findDropTarget` and possibly
 * `getIndexOfChildNode` and `move` to allow for custom to/from keys.
 *
 * For maximum control, `startDrag` and `evtDrop` can be overriden.
 */
export declare class DragDropPanel extends DragDropPanelBase {
    /**
     * Called when a widget should be moved as a consequence of an internal drag event.
     *
     * The default implementation assumes the keys `from` and `to` are numbers
     * indexing the drag panel's direct children. It then moves the child at the
     * `to` key to the location of the `from` key.
     */
    protected move(from: any, to: any): void;
    /**
     * Returns a key used to represent the child node.
     *
     * The default implementation returns the index of node in
     * `this.layout.widgets`.
     *
     * Returns null if not found.
     */
    protected getIndexOfChildNode(node: HTMLElement | null, parent?: PanelLayout): any;
    /**
     * Adds mime data represeting the drag data to the drag event's MimeData bundle.
     *
     * The default implementation adds mime data indicating the index of the direct
     * child being dragged (as indicated by findDragTarget).
     *
     * Override this method if you have data that cannot be communicated well by an
     * index, for example if the data should be able to be dropped on an external
     * target that only understands direct mime data.
     *
     * As the method simply adds mime data for a specific key, overriders can call
     * this method before/after adding their own mime data to still support default
     * dragging behavior.
     */
    protected addMimeData(handle: HTMLElement, mimeData: MimeData): void;
    /**
     * Processes a drop event.
     *
     * This function is called after checking:
     *  - That the `dropTarget` is a valid drop target
     *  - The value of `event.source` if `acceptDropsFromExternalSource` is false
     *
     * The default implementation assumes calling `getIndexOfChildNode` with
     * `dropTarget` will be valid. It will call `move` with that index as `to`,
     * and the index stored in the mime data as `from`.
     *
     * Override this if you need to handle other mime data than the default.
     */
    protected processDrop(dropTarget: HTMLElement, event: IDragEvent): void;
}
/**
 * The namespace for the `DropPanel` class statics.
 */
export declare namespace DropPanel {
    /**
     * An options object for initializing a drag panel widget.
     */
    interface IOptions extends Panel.IOptions {
        /**
         * Whether the lsit should accept drops from an external source.
         * Defaults to false.
         *
         * This option only makes sense to set for subclasses that accept drops from
         * external sources.
         */
        acceptDropsFromExternalSource?: boolean;
    }
    /**
     * Validate a drop action against a SupportedActions type
     */
    function isValidAction(supported: SupportedActions, action: DropAction): boolean;
}
/**
 * The namespace for the `DragPanel` class statics.
 */
export declare namespace DragPanel {
    /**
     * An options object for initializing a drag panel widget.
     */
    interface IOptions extends Panel.IOptions {
        /**
         * Whether all direct children of the list are handles, or only those widgets
         * designated as handles. Defaults to false.
         */
        childrenAreDragHandles?: boolean;
    }
    /**
     * Mark a widget as a drag handle.
     *
     * Using this, any child-widget can be a drag handle, as long as mouse events
     * are propagated from it to the DragPanel.
     */
    function makeHandle(handle: Widget): void;
    /**
     * Unmark a widget as a drag handle
     */
    function unmakeHandle(handle: Widget): void;
    /**
     * Create a default handle widget for dragging (see styling in DragPanel.css).
     *
     * The handle will need to be styled to ensure a minimum size
     */
    function createDefaultHandle(): Widget;
}
/**
 * The namespace for the `DragDropPanel` class statics.
 */
export declare namespace DragDropPanel {
    interface IOptions extends DragPanel.IOptions, DropPanel.IOptions {
    }
}
export declare class FriendlyDragDrop extends DragDropPanel {
    private static _counter;
    private static _groups;
    static makeGroup(): number;
    setFriendlyGroup(id: number): void;
    addToFriendlyGroup(other: FriendlyDragDrop): void;
    get friends(): FriendlyDragDrop[];
    protected getIndexOfChildNode(node: HTMLElement, parent?: PanelLayout): any;
    private _groupId;
    protected validateSource(event: IDragEvent): boolean;
}
//# sourceMappingURL=dragpanel.d.ts.map