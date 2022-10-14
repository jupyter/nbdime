"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.FlexLayout = void 0;
/*-----------------------------------------------------------------------------
| Copyright (c) 2014-2016, PhosphorJS Contributors
|
| Distributed under the terms of the BSD 3-Clause License.
|
| The full license is in the file LICENSE, distributed with this software.
|----------------------------------------------------------------------------*/
const algorithm_1 = require("@lumino/algorithm");
const messaging_1 = require("@lumino/messaging");
const widgets_1 = require("@lumino/widgets");
/**
 * The class name added to left-to-right flex layout parents.
 */
const LEFT_TO_RIGHT_CLASS = 'p-mod-left-to-right';
/**
 * The class name added to right-to-left flex layout parents.
 */
const RIGHT_TO_LEFT_CLASS = 'p-mod-right-to-left';
/**
 * The class name added to top-to-bottom flex layout parents.
 */
const TOP_TO_BOTTOM_CLASS = 'p-mod-top-to-bottom';
/**
 * The class name added to bottom-to-top flex layout parents.
 */
const BOTTOM_TO_TOP_CLASS = 'p-mod-bottom-to-top';
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
class FlexLayout extends widgets_1.PanelLayout {
    /**
     * Construct a new flex layout.
     *
     * @param options - The options for initializing the layout.
     */
    constructor(options = {}) {
        super();
        /**
         * Manage the display order of the widgets via the flexbox
         * attribute `order`, while keeping the internal DOM order
         * intact.
         */
        this.order = null;
        this._wrap = false;
        this._minimumSpacing = 4;
        this._justifyContent = null;
        this._alignItems = null;
        this._alignContent = null;
        this._dirty = false;
        this._direction = 'top-to-bottom';
        this._stretchType = null;
        this._evenSizes = false;
        if (options.direction !== void 0) {
            this._direction = options.direction;
        }
        if (options.minimumSpacing !== void 0) {
            this._minimumSpacing = Private.clampSpacing(options.minimumSpacing);
        }
        if (options.wrap !== void 0) {
            this._wrap = options.wrap;
        }
        if (options.justifyContent !== void 0) {
            this._justifyContent = options.justifyContent;
        }
        if (options.alignItems !== void 0) {
            this._alignItems = options.alignItems;
        }
        if (options.alignContent !== void 0) {
            this._alignContent = options.alignContent;
        }
        if (options.stretchType !== void 0) {
            this._stretchType = options.stretchType;
        }
        if (options.evenSizes !== void 0) {
            this._evenSizes = options.evenSizes;
        }
    }
    /**
     * Get the layout direction for the flex layout.
     */
    get direction() {
        return this._direction;
    }
    /**
     * Set the layout direction for the flex layout.
     */
    set direction(value) {
        if (this._direction === value) {
            return;
        }
        this._direction = value;
        if (!this.parent) {
            return;
        }
        Private.toggleDirection(this.parent, value);
        this.parent.fit();
    }
    /**
     * Get the minimum inter-element spacing for the flex layout.
     */
    get minimumSpacing() {
        return this._minimumSpacing;
    }
    /**
     * Set the minimum inter-element spacing for the flex layout.
     */
    set minimumSpacing(value) {
        value = Private.clampSpacing(value);
        if (this._minimumSpacing === value) {
            return;
        }
        this._minimumSpacing = value;
        if (!this.parent) {
            return;
        }
        this.parent.node.style.flexWrap = value ? 'wrap' : 'nowrap';
        this.parent.fit();
    }
    /**
     * Whether the layout should wrap its children if they do not all fit in
     * column/row.
     */
    get wrap() {
        return this._wrap;
    }
    set wrap(value) {
        if (this._wrap === value) {
            return;
        }
        this._wrap = value;
        if (!this.parent) {
            return;
        }
        this.parent.node.style.flexWrap = value ? 'wrap' : 'nowrap';
        this.parent.fit();
    }
    /**
     * Controls how to align children in the direction of the layout.
     */
    get justifyContent() {
        return this._justifyContent;
    }
    set justifyContent(value) {
        if (this._justifyContent === value) {
            return;
        }
        this._justifyContent = value;
        let flex = Private.translateFlexString(value);
        if (!this.parent) {
            return;
        }
        this.parent.node.style.justifyContent = flex;
        this.parent.fit();
    }
    /**
     * Controls how to align children in the direction perpendicular to that
     * of the layout (for a horizontal layout the will be the vertical align,
     * and vice-versa).
     */
    get alignItems() {
        return this._alignItems;
    }
    set alignItems(value) {
        if (this._alignItems === value) {
            return;
        }
        this._alignItems = value;
        let flex = Private.translateFlexString(value);
        if (!this.parent) {
            return;
        }
        this.parent.node.style.alignItems = flex;
        this.parent.fit();
    }
    /**
     * If layout is set to wrap, this defines how the wrapped lines will be
     * aligned in relation ro each other.
     */
    get alignContent() {
        return this._alignContent;
    }
    set alignContent(value) {
        if (this._alignContent === value) {
            return;
        }
        this._alignContent = value;
        let flex = Private.translateFlexString(value);
        if (!this.parent) {
            return;
        }
        this.parent.node.style.alignContent = flex;
        // Setting has no effect unless wrap is true, but
        // check against false to accomodate unset scenario
        // where CSS rules might apply:
        if (this._wrap !== false) {
            this.parent.fit();
        }
    }
    /**
     * Describe how to stretch items to fit into flex panel.
     */
    get stretchType() {
        return this._stretchType;
    }
    set stretchType(value) {
        if (this._stretchType === value) {
            return;
        }
        this._stretchType = value;
        if (!this.parent) {
            return;
        }
        this.parent.fit();
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
        return this._evenSizes;
    }
    set evenSizes(value) {
        if (this._evenSizes === value) {
            return;
        }
        this._evenSizes = value;
        if (!this.parent) {
            return;
        }
        this.parent.fit();
    }
    /**
     * Determine whether direction is a horizontal one
     */
    isHorizontal() {
        return this.direction === 'right-to-left' || this.direction === 'left-to-right';
    }
    /**
     * Determine whether direction is a vertical one
     */
    isVertical() {
        return !this.isHorizontal();
    }
    /**
     * Perform layout initialization which requires the parent widget.
     */
    init() {
        Private.toggleDirection(this.parent, this.direction);
        super.init();
    }
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
    attachWidget(index, widget) {
        // Call super implmentation
        super.attachWidget(index, widget);
        // Set order, if applicable
        if (this.order) {
            algorithm_1.ArrayExt.insert(this.order, index, widget);
        }
        // Post a layout request for the parent widget.
        this.parent.fit();
    }
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
    moveWidget(fromIndex, toIndex, widget) {
        if (fromIndex !== toIndex) {
            // Change the order of the widget.
            if (!this.order) {
                this.order = this.widgets.slice();
            }
            algorithm_1.ArrayExt.move(this.order, fromIndex, toIndex);
            this._dirty = true;
        }
        // Post an update request for the parent widget.
        this.parent.update();
    }
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
    detachWidget(index, widget) {
        // Remove widget from order vector
        if (this.order) {
            let i = 0;
            for (; i < this.order.length; ++i) {
                if (widget === this.order[i]) {
                    algorithm_1.ArrayExt.removeAt(this.order, i);
                    break;
                }
            }
        }
        // Call super implmentation
        super.detachWidget(index, widget);
        // Post a layout request for the parent widget.
        this.parent.fit();
    }
    /**
     * A message handler invoked on an `'after-show'` message.
     */
    onAfterShow(msg) {
        super.onAfterShow(msg);
        this.parent.update();
    }
    /**
     * A message handler invoked on an `'after-attach'` message.
     */
    onAfterAttach(msg) {
        super.onAfterAttach(msg);
        Private.toggleDirection(this.parent, this._direction);
        let style = this.parent.node.style;
        style.flexWrap = this._wrap ? 'wrap' : 'nowrap';
        style.justifyContent = Private.translateFlexString(this._justifyContent) || '';
        style.alignContent = Private.translateFlexString(this._alignContent) || '';
        style.alignItems = Private.translateFlexString(this._alignItems) || '';
        this.parent.fit();
    }
    /**
     * A message handler invoked on a `'child-shown'` message.
     */
    onChildShown(msg) {
        this.parent.fit();
    }
    /**
     * A message handler invoked on a `'child-hidden'` message.
     */
    onChildHidden(msg) {
        this.parent.fit();
    }
    /**
     * A message handler invoked on a `'resize'` message.
     */
    onResize(msg) {
        if (this.parent.isVisible) {
            this._update();
        }
    }
    /**
     * A message handler invoked on an `'update-request'` message.
     */
    onUpdateRequest(msg) {
        if (this.parent.isVisible) {
            this._update();
        }
    }
    /**
     * A message handler invoked on a `'fit-request'` message.
     */
    onFitRequest(msg) {
        if (this.parent.isAttached) {
            this._fit();
        }
    }
    /**
     * Fit the layout to the total size required by the widgets.
     */
    _fit() {
        // Set the dirty flag to ensure only a single update occurs.
        this._dirty = true;
        // Notify the ancestor that it should fit immediately. This may
        // cause a resize of the parent, fulfilling the required update.
        let ancestor = this.parent.parent;
        if (ancestor) {
            messaging_1.MessageLoop.sendMessage(ancestor, widgets_1.Widget.Msg.FitRequest);
        }
        // If the dirty flag is still set, the parent was not resized.
        // Trigger the required update on the parent widget immediately.
        if (this._dirty) {
            messaging_1.MessageLoop.sendMessage(this.parent, widgets_1.Widget.Msg.UpdateRequest);
        }
    }
    /**
     * Update the layout position and size of the widgets.
     *
     * The parent offset dimensions should be `-1` if unknown.
     */
    _update() {
        // Clear the dirty flag to indicate the update occurred.
        this._dirty = false;
        // Bail early if there are no widgets to layout.
        let widgets = this.order || this.widgets;
        if (widgets.length === 0) {
            return;
        }
        // Set spacing by margins
        let spacing = this.minimumSpacing.toString() + 'px';
        if (this.isHorizontal()) {
            for (let i = 0; i < widgets.length - 1; ++i) {
                widgets[i].node.style.marginRight = spacing;
            }
        }
        else {
            for (let i = 0; i < widgets.length - 1; ++i) {
                widgets[i].node.style.marginBottom = spacing;
            }
        }
        // Update stretch styles if set
        if (this._evenSizes || this.stretchType) {
            let basis = null;
            let grow = null;
            let shrink = null;
            if (this._evenSizes) {
                basis = 0;
                grow = 1;
            }
            else {
                switch (this._stretchType) {
                    case 'grow':
                        // Allow items to grow from default size
                        grow = 1;
                        shrink = 0;
                        break;
                    case 'shrink':
                        // Allow items to shrink from default size
                        grow = 0;
                        shrink = 1;
                        break;
                    case 'both':
                        // Both growing and shrinking is allowed.
                        grow = 1;
                        shrink = 1;
                        break;
                    case 'fixed':
                        // Disallow both growing and shrinking.
                        grow = 0;
                        shrink = 0;
                        break;
                    default:
                        throw new TypeError('Invalid stretch type: ' + this._stretchType);
                }
            }
            for (let i = 0; i < widgets.length; ++i) {
                let style = widgets[i].node.style;
                if (basis !== null) {
                    // Can only be 0, so no unit needed
                    style.flexBasis = basis.toString();
                }
                if (grow !== null) {
                    style.flexGrow = grow.toString();
                }
                if (shrink !== null) {
                    style.flexShrink = shrink.toString();
                }
            }
        }
        // Update display order
        for (let i = 0; i < widgets.length; ++i) {
            let widget = widgets[i];
            widget.node.style.order = this.order ? i.toString() : '';
        }
    }
}
exports.FlexLayout = FlexLayout;
/**
 * The namespace for the `FlexLayout` class statics.
 */
(function (FlexLayout) {
    /**
     * Get the flex-grow number of the widget
     */
    function getGrow(widget) {
        let value = widget.node.style.flexGrow;
        return value ? parseInt(value, 10) : null;
    }
    FlexLayout.getGrow = getGrow;
    /**
     * Set the flex-grow number of the widget
     */
    function setGrow(widget, value, fit = true) {
        widget.node.style.flexGrow = value === null ? '' : value.toString();
        if (fit && widget.parent) {
            widget.parent.fit();
        }
    }
    FlexLayout.setGrow = setGrow;
    /**
     * Get the flex-shrink number of the widget
     */
    function getShrink(widget) {
        let value = widget.node.style.flexShrink;
        return value ? parseInt(value, 10) : null;
    }
    FlexLayout.getShrink = getShrink;
    /**
     * Set the flex-shrink number of the widget
     */
    function setShrink(widget, value, fit = true) {
        widget.node.style.flexShrink = value === null ? '' : value.toString();
        if (fit && widget.parent) {
            widget.parent.fit();
        }
    }
    FlexLayout.setShrink = setShrink;
    /**
     * Get the size basis of the widget.
     */
    function getSizeBasis(widget) {
        let value = widget.node.style.flexBasis;
        if (value === 'auto') {
            return 'auto';
        }
        else {
            return value ? parseInt(value.replace('px', ''), 10) : null;
        }
    }
    FlexLayout.getSizeBasis = getSizeBasis;
    /**
     * Set the size basis of the widget.
     *
     * This is the value used for calculating how to distribute positive
     * (grow) or negatie (shrink) free space in a flex box. The value
     * `'auto'` uses the `width`/`height` field of the box as the basis.
     */
    function setSizeBasis(widget, value, fit = true) {
        if (value === 'auto') {
            widget.node.style.flexBasis = value;
        }
        else if (value === null) {
            widget.node.style.flexBasis = '';
        }
        else {
            widget.node.style.flexBasis = value.toString() + 'px';
        }
        if (fit && widget.parent) {
            widget.parent.fit();
        }
    }
    FlexLayout.setSizeBasis = setSizeBasis;
})(FlexLayout = exports.FlexLayout || (exports.FlexLayout = {}));
/**
 * The namespace for the private module data.
 */
var Private;
(function (Private) {
    /**
     * Test whether a direction has horizontal orientation.
     */
    function isHorizontal(dir) {
        return dir === 'left-to-right' || dir === 'right-to-left';
    }
    Private.isHorizontal = isHorizontal;
    function translateFlexString(value) {
        if (value === 'start' || value === 'end') {
            value = 'flex-' + value;
        }
        return value;
    }
    Private.translateFlexString = translateFlexString;
    /**
     * Toggle the CSS direction class for the given widget.
     */
    function toggleDirection(widget, dir) {
        widget.toggleClass(LEFT_TO_RIGHT_CLASS, dir === 'left-to-right');
        widget.toggleClass(RIGHT_TO_LEFT_CLASS, dir === 'right-to-left');
        widget.toggleClass(TOP_TO_BOTTOM_CLASS, dir === 'top-to-bottom');
        widget.toggleClass(BOTTOM_TO_TOP_CLASS, dir === 'bottom-to-top');
    }
    Private.toggleDirection = toggleDirection;
    /**
     * Clamp a spacing value to an integer >= 0.
     */
    function clampSpacing(value) {
        return Math.max(0, Math.floor(value));
    }
    Private.clampSpacing = clampSpacing;
})(Private || (Private = {}));
//# sourceMappingURL=flexlayout.js.map