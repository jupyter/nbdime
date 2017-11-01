/*-----------------------------------------------------------------------------
| Copyright (c) 2014-2016, PhosphorJS Contributors
|
| Distributed under the terms of the BSD 3-Clause License.
|
| The full license is in the file LICENSE, distributed with this software.
|----------------------------------------------------------------------------*/
import {
  Message
} from '@phosphor/messaging';

import {
  FlexLayout
} from './flexlayout';

import {
  Panel, Widget
} from '@phosphor/widgets';


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
export
class FlexPanel extends Panel {
  /**
   * Construct a new flex panel.
   *
   * @param options - The options for initializing the flex panel.
   */
  constructor(options: FlexPanel.IOptions = {}) {
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
  get direction(): FlexPanel.Direction {
    return this.layout.direction;
  };

  set direction(value: FlexPanel.Direction) {
    this.layout.direction = value;
  }

  /**
   * The minimum inter-element spacing for the flex panel.
   */
  get minimumSpacing(): number {
    return this.layout.minimumSpacing;
  };

  set minimumSpacing(value: number) {
    this.layout.minimumSpacing = value;
  }

  /**
   * Whether the layout should wrap its children if they do not all fit in
   * column/row.
   */
  get wrap(): boolean {
    return this.layout.wrap;
  };

  set wrap(value: boolean) {
    this.layout.wrap = value;
  }

  /**
   * Controls how to align children in the direction of the layout.
   */
  get justifyContent(): FlexPanel.ContentJustification | null {
    return this.layout.justifyContent;
  };

  set justifyContent(value: FlexPanel.ContentJustification | null) {
    this.layout.justifyContent = value;
  }

  /**
   * Controls how to align children in the direction perpendicular to that
   * of the layout (for a horizontal layout the will be the vertical align,
   * and vice-versa).
   */
  get alignItems(): FlexPanel.ItemAlignment | null {
    return this.layout.alignItems;
  };

  set alignItems(value: FlexPanel.ItemAlignment | null) {
    this.layout.alignItems = value;
  }

  /**
   * If layout is set to wrap, this defines how the wrapped lines will be
   * aligned in relation ro each other.
   */
  get alignContent(): FlexPanel.ContentAlignment | null {
    return this.layout.alignContent;
  };

  set alignContent(value: FlexPanel.ContentAlignment | null) {
    this.layout.alignContent = value;
  }

  /**
   * Describe how to stretch items to fit into flex panel.
   */
  get stretchType(): FlexPanel.StretchType | null {
    return this.layout.stretchType;
  };

  set stretchType(value: FlexPanel.StretchType | null) {
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
  get evenSizes(): boolean {
    return this.layout.evenSizes;
  };

  set evenSizes(value: boolean) {
    this.layout.evenSizes = value;
  };

  /**
   * A message handler invoked on a `'child-added'` message.
   */
  protected onChildAdded(msg: Widget.ChildMessage): void {
    msg.child.addClass(CHILD_CLASS);
  }

  /**
   * A message handler invoked on a `'child-removed'` message.
   */
  protected onChildRemoved(msg: Widget.ChildMessage): void {
    msg.child.removeClass(CHILD_CLASS);
  }

  /**
   * A message handler invoked on an `'after-attach'` message.
   */
  protected onAfterAttach(msg: Message): void {
    super.onAfterAttach(msg);
    this.fit();
  }

  layout: FlexLayout;
}

/**
 * The namespace for the `FlexPanel` class statics.
 */
export
namespace FlexPanel {
  /**
   * A type alias for a flex panel direction.
   */
  export
  type Direction = FlexLayout.Direction;
  /**
   * A type alias for a flex panel direction.
   */
  export
  type ContentJustification = FlexLayout.ContentJustification;
  /**
   * A type alias for a flex panel direction.
   */
  export
  type ContentAlignment = FlexLayout.ContentAlignment;
  /**
   * A type alias for a flex panel direction.
   */
  export
  type ItemAlignment = FlexLayout.ItemAlignment;
  /**
   * A type alias for a flex panel direction.
   */
  export
  type StretchType = FlexLayout.StretchType;

  /**
   * An options object for initializing a flex panel.
   */
  export
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
  export
  function getGrow(widget: Widget): number | null {
    return FlexLayout.getGrow(widget);
  }

  /**
   * Set the flex panel grow factor for the given widget.
   *
   * @param widget - The widget of interest.
   *
   * @param value - The value for the grow factor.
   */
  export
  function setGrow(widget: Widget, value: number): void {
    FlexLayout.setGrow(widget, value);
  }

  /**
   * Get the flex panel shrink factor for the given widget.
   *
   * @param widget - The widget of interest.
   *
   * @returns The flex panel shrink factor for the widget.
   */
  export
  function getShrink(widget: Widget): number | null {
    return FlexLayout.getShrink(widget);
  }

  /**
   * Set the flex panel shrink factor for the given widget.
   *
   * @param widget - The widget of interest.
   *
   * @param value - The value for the shrink factor.
   */
  export
  function setShrink(widget: Widget, value: number | null): void {
    FlexLayout.setShrink(widget, value);
  }

  /**
   * Get the flex panel size basis for the given widget.
   *
   * @param widget - The widget of interest.
   *
   * @returns The flex panel size basis for the widget.
   */
  export
  function getSizeBasis(widget: Widget): number | "auto" | null {
    return FlexLayout.getSizeBasis(widget);
  }

  /**
   * Set the flex panel size basis for the given widget.
   *
   * @param widget - The widget of interest.
   *
   * @param value - The value for the size basis.
   */
  export
  function setSizeBasis(widget: Widget, value: number | "auto" | null): void {
    FlexLayout.setSizeBasis(widget, value);
  }
}

/**
 * The namespace for the private module data.
 */
namespace Private {
  /**
   * Create a flex layout for the given panel options.
   */
  export
  function createLayout(options: FlexPanel.IOptions): FlexLayout {
    return options.layout || new FlexLayout(options);
  }
}