"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.FlexPanel = void 0;
const flexlayout_1 = require("./flexlayout");
const widgets_1 = require("@lumino/widgets");
/**
 * The class name added to FlexPanel instances.
 */
const FLEX_PANEL_CLASS = 'p-FlexPanel';
/**
 * The class name added to a FlexPanel child.
 */
const CHILD_CLASS = 'p-FlexPanel-child';
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
class FlexPanel extends widgets_1.Panel {
    /**
     * Construct a new flex panel.
     *
     * @param options - The options for initializing the flex panel.
     */
    constructor(options = {}) {
        super({ layout: Private.createLayout(options) });
        if (!options.layout) {
            if (options.minimumSpacing !== void 0) {
                this.minimumSpacing = options.minimumSpacing;
            }
            if (options.direction !== void 0) {
                this.direction = options.direction;
            }
        }
        this.addClass(FLEX_PANEL_CLASS);
    }
    /**
     * The layout direction for the flex panel.
     */
    get direction() {
        return this.layout.direction;
    }
    ;
    set direction(value) {
        this.layout.direction = value;
    }
    /**
     * The minimum inter-element spacing for the flex panel.
     */
    get minimumSpacing() {
        return this.layout.minimumSpacing;
    }
    ;
    set minimumSpacing(value) {
        this.layout.minimumSpacing = value;
    }
    /**
     * Whether the layout should wrap its children if they do not all fit in
     * column/row.
     */
    get wrap() {
        return this.layout.wrap;
    }
    ;
    set wrap(value) {
        this.layout.wrap = value;
    }
    /**
     * Controls how to align children in the direction of the layout.
     */
    get justifyContent() {
        return this.layout.justifyContent;
    }
    ;
    set justifyContent(value) {
        this.layout.justifyContent = value;
    }
    /**
     * Controls how to align children in the direction perpendicular to that
     * of the layout (for a horizontal layout the will be the vertical align,
     * and vice-versa).
     */
    get alignItems() {
        return this.layout.alignItems;
    }
    ;
    set alignItems(value) {
        this.layout.alignItems = value;
    }
    /**
     * If layout is set to wrap, this defines how the wrapped lines will be
     * aligned in relation ro each other.
     */
    get alignContent() {
        return this.layout.alignContent;
    }
    ;
    set alignContent(value) {
        this.layout.alignContent = value;
    }
    /**
     * Describe how to stretch items to fit into flex panel.
     */
    get stretchType() {
        return this.layout.stretchType;
    }
    ;
    set stretchType(value) {
        this.layout.stretchType = value;
    }
    /**
     * If set, the free space is distributed such that the
     * children are all the same size. Defaults to `false`.
     *
     * ### Notes
     * Setting this to `true` will make the layout
     * ignore the setting of `stretchType`.
     */
    get evenSizes() {
        return this.layout.evenSizes;
    }
    ;
    set evenSizes(value) {
        this.layout.evenSizes = value;
    }
    ;
    /**
     * A message handler invoked on a `'child-added'` message.
     */
    onChildAdded(msg) {
        msg.child.addClass(CHILD_CLASS);
    }
    /**
     * A message handler invoked on a `'child-removed'` message.
     */
    onChildRemoved(msg) {
        msg.child.removeClass(CHILD_CLASS);
    }
    /**
     * A message handler invoked on an `'after-attach'` message.
     */
    onAfterAttach(msg) {
        super.onAfterAttach(msg);
        this.fit();
    }
}
exports.FlexPanel = FlexPanel;
/**
 * The namespace for the `FlexPanel` class statics.
 */
(function (FlexPanel) {
    /**
     * Get the flex panel grow factor for the given widget.
     *
     * @param widget - The widget of interest.
     *
     * @returns The flex panel grow factor for the widget.
     */
    function getGrow(widget) {
        return flexlayout_1.FlexLayout.getGrow(widget);
    }
    FlexPanel.getGrow = getGrow;
    /**
     * Set the flex panel grow factor for the given widget.
     *
     * @param widget - The widget of interest.
     *
     * @param value - The value for the grow factor.
     */
    function setGrow(widget, value) {
        flexlayout_1.FlexLayout.setGrow(widget, value);
    }
    FlexPanel.setGrow = setGrow;
    /**
     * Get the flex panel shrink factor for the given widget.
     *
     * @param widget - The widget of interest.
     *
     * @returns The flex panel shrink factor for the widget.
     */
    function getShrink(widget) {
        return flexlayout_1.FlexLayout.getShrink(widget);
    }
    FlexPanel.getShrink = getShrink;
    /**
     * Set the flex panel shrink factor for the given widget.
     *
     * @param widget - The widget of interest.
     *
     * @param value - The value for the shrink factor.
     */
    function setShrink(widget, value) {
        flexlayout_1.FlexLayout.setShrink(widget, value);
    }
    FlexPanel.setShrink = setShrink;
    /**
     * Get the flex panel size basis for the given widget.
     *
     * @param widget - The widget of interest.
     *
     * @returns The flex panel size basis for the widget.
     */
    function getSizeBasis(widget) {
        return flexlayout_1.FlexLayout.getSizeBasis(widget);
    }
    FlexPanel.getSizeBasis = getSizeBasis;
    /**
     * Set the flex panel size basis for the given widget.
     *
     * @param widget - The widget of interest.
     *
     * @param value - The value for the size basis.
     */
    function setSizeBasis(widget, value) {
        flexlayout_1.FlexLayout.setSizeBasis(widget, value);
    }
    FlexPanel.setSizeBasis = setSizeBasis;
})(FlexPanel = exports.FlexPanel || (exports.FlexPanel = {}));
/**
 * The namespace for the private module data.
 */
var Private;
(function (Private) {
    /**
     * Create a flex layout for the given panel options.
     */
    function createLayout(options) {
        return options.layout || new flexlayout_1.FlexLayout(options);
    }
    Private.createLayout = createLayout;
})(Private || (Private = {}));
//# sourceMappingURL=flexpanel.js.map