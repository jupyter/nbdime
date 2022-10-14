import { Message } from '@lumino/messaging';
import { PanelLayout, Widget } from '@lumino/widgets';
/**
 * A layout which arranges its widgets in a single row or column.
 *
 * Use the direction attribute to specify the layout direction.
 *
 * The sizing and flow of the children can be specified in several ways:
 *  - The container level properties `minimumSpacing`,`wrap`,
 *    `justifyContent`, `alignItems` and `alignContent`.
 *  - The stretching of the children in the layout direction either by:
 *    - Setting individual values per widget of grow/shrink/basis by
 *      `setGrow`, `setShrink` and `setSizeBasis`.
 *    - Using the convenience attributes `evenSizes` or `stretchType`.
 *  - Manually by CSS using the flexbox CSS attribute for the classes
 *    `p-FlexPanel` and `p-FlexPanel-child`.
 */
export declare class FlexLayout extends PanelLayout {
    /**
     * Construct a new flex layout.
     *
     * @param options - The options for initializing the layout.
     */
    constructor(options?: FlexLayout.IOptions);
    /**
     * Get the layout direction for the flex layout.
     */
    get direction(): FlexLayout.Direction;
    /**
     * Set the layout direction for the flex layout.
     */
    set direction(value: FlexLayout.Direction);
    /**
     * Get the minimum inter-element spacing for the flex layout.
     */
    get minimumSpacing(): number;
    /**
     * Set the minimum inter-element spacing for the flex layout.
     */
    set minimumSpacing(value: number);
    /**
     * Whether the layout should wrap its children if they do not all fit in
     * column/row.
     */
    get wrap(): boolean;
    set wrap(value: boolean);
    /**
     * Controls how to align children in the direction of the layout.
     */
    get justifyContent(): FlexLayout.ContentJustification | null;
    set justifyContent(value: FlexLayout.ContentJustification | null);
    /**
     * Controls how to align children in the direction perpendicular to that
     * of the layout (for a horizontal layout the will be the vertical align,
     * and vice-versa).
     */
    get alignItems(): FlexLayout.ItemAlignment | null;
    set alignItems(value: FlexLayout.ItemAlignment | null);
    /**
     * If layout is set to wrap, this defines how the wrapped lines will be
     * aligned in relation ro each other.
     */
    get alignContent(): FlexLayout.ContentAlignment | null;
    set alignContent(value: FlexLayout.ContentAlignment | null);
    /**
     * Describe how to stretch items to fit into flex panel.
     */
    get stretchType(): FlexLayout.StretchType | null;
    set stretchType(value: FlexLayout.StretchType | null);
    /**
     * If set, the free space is distributed such that the
     * children are all the same size. Defaults to `false`.
     *
     * ### Notes
     * Setting this to `true` will make the layout
     * ignore the setting of `stretchType`.
     */
    get evenSizes(): boolean;
    set evenSizes(value: boolean);
    /**
     * Determine whether direction is a horizontal one
     */
    isHorizontal(): boolean;
    /**
     * Determine whether direction is a vertical one
     */
    isVertical(): boolean;
    /**
     * Perform layout initialization which requires the parent widget.
     */
    protected init(): void;
    /**
     * Attach a widget to the parent's DOM node.
     *
     * @param index - The current index of the widget in the layout.
     *
     * @param widget - The widget to attach to the parent.
     *
     * #### Notes
     * This is a reimplementation of the superclass method.
     */
    protected attachWidget(index: number, widget: Widget): void;
    /**
     * Change a widget's display order.
     *
     * @param fromIndex - The previous index of the widget in the layout.
     *
     * @param toIndex - The current index of the widget in the layout.
     *
     * @param widget - The widget to move in the parent.
     *
     * #### Notes
     * This is a reimplementation of the superclass method.
     */
    protected moveWidget(fromIndex: number, toIndex: number, widget: Widget): void;
    /**
     * Detach a widget from the parent's DOM node.
     *
     * @param index - The previous index of the widget in the layout.
     *
     * @param widget - The widget to detach from the parent.
     *
     * #### Notes
     * This is a reimplementation of the superclass method.
     */
    protected detachWidget(index: number, widget: Widget): void;
    /**
     * A message handler invoked on an `'after-show'` message.
     */
    protected onAfterShow(msg: Message): void;
    /**
     * A message handler invoked on an `'after-attach'` message.
     */
    protected onAfterAttach(msg: Message): void;
    /**
     * A message handler invoked on a `'child-shown'` message.
     */
    protected onChildShown(msg: Widget.ChildMessage): void;
    /**
     * A message handler invoked on a `'child-hidden'` message.
     */
    protected onChildHidden(msg: Widget.ChildMessage): void;
    /**
     * A message handler invoked on a `'resize'` message.
     */
    protected onResize(msg: Widget.ResizeMessage): void;
    /**
     * A message handler invoked on an `'update-request'` message.
     */
    protected onUpdateRequest(msg: Message): void;
    /**
     * A message handler invoked on a `'fit-request'` message.
     */
    protected onFitRequest(msg: Message): void;
    /**
     * Manage the display order of the widgets via the flexbox
     * attribute `order`, while keeping the internal DOM order
     * intact.
     */
    protected order: Widget[] | null;
    /**
     * Fit the layout to the total size required by the widgets.
     */
    private _fit;
    /**
     * Update the layout position and size of the widgets.
     *
     * The parent offset dimensions should be `-1` if unknown.
     */
    private _update;
    private _wrap;
    private _minimumSpacing;
    private _justifyContent;
    private _alignItems;
    private _alignContent;
    private _dirty;
    private _direction;
    private _stretchType;
    private _evenSizes;
}
/**
 * The namespace for the `FlexLayout` class statics.
 */
export declare namespace FlexLayout {
    /**
     * A type alias for a flex layout direction.
     */
    type Direction = ('left-to-right' | 'right-to-left' | 'top-to-bottom' | 'bottom-to-top');
    /**
     * Describes how to align children in the direction of the layout.
     */
    type ContentJustification = 'start' | 'end' | 'center' | 'space-between' | 'space-around';
    /**
     * If layout is set to wrap, this defines how the wrapped lines will be
     * aligned in relation ro each other.
     */
    type ContentAlignment = ContentJustification | 'stretch';
    /**
     * Controls how to align children in the direction perpendicular to that
     * of the layout (for a horizontal layout the will be the vertical align,
     * and vice-versa).
     */
    type ItemAlignment = 'start' | 'end' | 'center' | 'baseline' | 'stretch';
    /**
     * Describe how to stretch items to fit into flex panel:
     * 'grow': Allow items to grow from default size
     * 'shrink': Allow items to shrink from default size
     * 'both': Both growing and shrinking is allowed.
     * 'fixed': Do not allow either growing or shrinking.
     */
    type StretchType = 'grow' | 'shrink' | 'both' | 'fixed';
    /**
     * An options object for initializing a flex layout.
     */
    interface IOptions {
        /**
         * The direction of the layout.
         *
         * The default is `'top-to-bottom'`.
         */
        direction?: Direction;
        /**
         * The minimum spacing between items in the layout.
         *
         * The default is `4`.
         */
        minimumSpacing?: number;
        /**
         * Whether the layout should wrap its children if they do not all fit in
         * column/row.
         */
        wrap?: boolean;
        /**
         * Controls how to align children in the direction of the layout.
         */
        justifyContent?: ContentJustification;
        /**
         * Controls how to align children in the direction perpendicular to that
         * of the layout (for a horizontal layout the will be the vertical align,
         * and vice-versa).
         */
        alignItems?: ItemAlignment;
        /**
         * If layout is set to wrap, this defines how the wrapped lines will be
         * aligned in relation ro each other.
         */
        alignContent?: ContentAlignment;
        /**
         * Describe how to stretch items to fit into flex panel.
         */
        stretchType?: StretchType;
        /**
         * If set, the free space is distributed such that the
         * children are all the same size. Defaults to `false`.
         *
         * ### Notes
         * Setting this to `true` will make the layout
         * ignore the setting of `stretchType`.
         */
        evenSizes?: boolean;
    }
    /**
     * Get the flex-grow number of the widget
     */
    function getGrow(widget: Widget): number | null;
    /**
     * Set the flex-grow number of the widget
     */
    function setGrow(widget: Widget, value: number, fit?: boolean): void;
    /**
     * Get the flex-shrink number of the widget
     */
    function getShrink(widget: Widget): number | null;
    /**
     * Set the flex-shrink number of the widget
     */
    function setShrink(widget: Widget, value: number | null, fit?: boolean): void;
    /**
     * Get the size basis of the widget.
     */
    function getSizeBasis(widget: Widget): number | 'auto' | null;
    /**
     * Set the size basis of the widget.
     *
     * This is the value used for calculating how to distribute positive
     * (grow) or negatie (shrink) free space in a flex box. The value
     * `'auto'` uses the `width`/`height` field of the box as the basis.
     */
    function setSizeBasis(widget: Widget, value: number | 'auto' | null, fit?: boolean): void;
}
//# sourceMappingURL=flexlayout.d.ts.map