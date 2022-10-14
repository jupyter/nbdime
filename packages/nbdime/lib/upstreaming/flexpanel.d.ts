import { Message } from '@lumino/messaging';
import { FlexLayout } from './flexlayout';
import { Panel, Widget } from '@lumino/widgets';
/**
 * A panel which arranges its widgets in a single row or column.
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
 *
 * #### Notes
 * This class provides a convenience wrapper around a [[FlexLayout]].
 */
export declare class FlexPanel extends Panel {
    /**
     * Construct a new flex panel.
     *
     * @param options - The options for initializing the flex panel.
     */
    constructor(options?: FlexPanel.IOptions);
    /**
     * The layout direction for the flex panel.
     */
    get direction(): FlexPanel.Direction;
    set direction(value: FlexPanel.Direction);
    /**
     * The minimum inter-element spacing for the flex panel.
     */
    get minimumSpacing(): number;
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
    get justifyContent(): FlexPanel.ContentJustification | null;
    set justifyContent(value: FlexPanel.ContentJustification | null);
    /**
     * Controls how to align children in the direction perpendicular to that
     * of the layout (for a horizontal layout the will be the vertical align,
     * and vice-versa).
     */
    get alignItems(): FlexPanel.ItemAlignment | null;
    set alignItems(value: FlexPanel.ItemAlignment | null);
    /**
     * If layout is set to wrap, this defines how the wrapped lines will be
     * aligned in relation ro each other.
     */
    get alignContent(): FlexPanel.ContentAlignment | null;
    set alignContent(value: FlexPanel.ContentAlignment | null);
    /**
     * Describe how to stretch items to fit into flex panel.
     */
    get stretchType(): FlexPanel.StretchType | null;
    set stretchType(value: FlexPanel.StretchType | null);
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
     * A message handler invoked on a `'child-added'` message.
     */
    protected onChildAdded(msg: Widget.ChildMessage): void;
    /**
     * A message handler invoked on a `'child-removed'` message.
     */
    protected onChildRemoved(msg: Widget.ChildMessage): void;
    /**
     * A message handler invoked on an `'after-attach'` message.
     */
    protected onAfterAttach(msg: Message): void;
    layout: FlexLayout;
}
/**
 * The namespace for the `FlexPanel` class statics.
 */
export declare namespace FlexPanel {
    /**
     * A type alias for a flex panel direction.
     */
    type Direction = FlexLayout.Direction;
    /**
     * A type alias for a flex panel direction.
     */
    type ContentJustification = FlexLayout.ContentJustification;
    /**
     * A type alias for a flex panel direction.
     */
    type ContentAlignment = FlexLayout.ContentAlignment;
    /**
     * A type alias for a flex panel direction.
     */
    type ItemAlignment = FlexLayout.ItemAlignment;
    /**
     * A type alias for a flex panel direction.
     */
    type StretchType = FlexLayout.StretchType;
    /**
     * An options object for initializing a flex panel.
     */
    interface IOptions extends FlexLayout.IOptions, Panel.IOptions {
        /**
         * The flex layout to use for the flex panel.
         *
         * If this is provided, the other options are ignored.
         *
         * The default is a new `FlexLayout`.
         */
        layout?: FlexLayout;
    }
    /**
     * Get the flex panel grow factor for the given widget.
     *
     * @param widget - The widget of interest.
     *
     * @returns The flex panel grow factor for the widget.
     */
    function getGrow(widget: Widget): number | null;
    /**
     * Set the flex panel grow factor for the given widget.
     *
     * @param widget - The widget of interest.
     *
     * @param value - The value for the grow factor.
     */
    function setGrow(widget: Widget, value: number): void;
    /**
     * Get the flex panel shrink factor for the given widget.
     *
     * @param widget - The widget of interest.
     *
     * @returns The flex panel shrink factor for the widget.
     */
    function getShrink(widget: Widget): number | null;
    /**
     * Set the flex panel shrink factor for the given widget.
     *
     * @param widget - The widget of interest.
     *
     * @param value - The value for the shrink factor.
     */
    function setShrink(widget: Widget, value: number | null): void;
    /**
     * Get the flex panel size basis for the given widget.
     *
     * @param widget - The widget of interest.
     *
     * @returns The flex panel size basis for the widget.
     */
    function getSizeBasis(widget: Widget): number | "auto" | null;
    /**
     * Set the flex panel size basis for the given widget.
     *
     * @param widget - The widget of interest.
     *
     * @param value - The value for the size basis.
     */
    function setSizeBasis(widget: Widget, value: number | "auto" | null): void;
}
//# sourceMappingURL=flexpanel.d.ts.map