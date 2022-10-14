// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
'use strict';
Object.defineProperty(exports, "__esModule", { value: true });
exports.CollapsiblePanel = void 0;
const widgets_1 = require("@lumino/widgets");
const COLLAPSIBLE_CLASS = 'jp-CollapsiblePanel';
const COLLAPSIBLE_HEADER = 'jp-CollapsiblePanel-header';
const COLLAPSIBLE_HEADER_ICON = 'jp-CollapsiblePanel-header-icon';
const COLLAPSIBLE_HEADER_ICON_OPEN = 'jp-CollapsiblePanel-header-icon-opened';
const COLLAPSIBLE_HEADER_ICON_CLOSED = 'jp-CollapsiblePanel-header-icon-closed';
const COLLAPSIBLE_SLIDER = 'jp-CollapsiblePanel-slider';
const COLLAPSIBLE_OPEN = 'jp-CollapsiblePanel-opened';
const COLLAPSIBLE_CLOSED = 'jp-CollapsiblePanel-closed';
const COLLAPSIBLE_CONTAINER = 'jp-CollapsiblePanel-container';
/**
 * CollapsiblePanel
 */
class CollapsiblePanel extends widgets_1.Panel {
    constructor(inner, headerTitle, collapsed) {
        super();
        this.addClass(COLLAPSIBLE_CLASS);
        this.inner = inner;
        let constructor = this.constructor;
        let header = constructor.createHeader(headerTitle);
        this.header = header;
        this.button = header.node.getElementsByClassName(COLLAPSIBLE_HEADER_ICON)[0];
        header.node.onclick = this.toggleCollapsed.bind(this);
        this.addWidget(header);
        this.container = new widgets_1.Panel();
        this.container.addClass(COLLAPSIBLE_CONTAINER);
        this.slider = new widgets_1.Panel();
        this.slider.addClass(COLLAPSIBLE_SLIDER);
        this.slider.addWidget(inner);
        this.container.addWidget(this.slider);
        this.addWidget(this.container);
        this.slider.addClass(collapsed === true ?
            COLLAPSIBLE_CLOSED :
            COLLAPSIBLE_OPEN);
        this.button.classList.add(collapsed === true ?
            COLLAPSIBLE_HEADER_ICON_CLOSED :
            COLLAPSIBLE_HEADER_ICON_OPEN);
        this.button.classList.add("fa");
        this.button.classList.add(collapsed === true ?
            "fa-caret-down" :
            "fa-caret-up");
    }
    static createHeader(headerTitle) {
        let header = new widgets_1.Panel();
        header.addClass(COLLAPSIBLE_HEADER);
        if (headerTitle) {
            // let title = document.createElement('span');
            header.node.innerText = headerTitle;
            // header.appendChild(title);
        }
        let button = document.createElement('button');
        button.className = COLLAPSIBLE_HEADER_ICON;
        header.node.appendChild(button);
        return header;
    }
    toggleCollapsed() {
        let slider = this.slider;
        let button = this.button;
        if (this.collapsed) {
            slider.removeClass(COLLAPSIBLE_CLOSED);
            slider.addClass(COLLAPSIBLE_OPEN);
            button.classList.remove(COLLAPSIBLE_HEADER_ICON_CLOSED);
            button.classList.add(COLLAPSIBLE_HEADER_ICON_OPEN);
            this.button.classList.remove("fa-caret-down");
            this.button.classList.add("fa-caret-up");
        }
        else {
            slider.removeClass(COLLAPSIBLE_OPEN);
            slider.addClass(COLLAPSIBLE_CLOSED);
            button.classList.remove(COLLAPSIBLE_HEADER_ICON_OPEN);
            button.classList.add(COLLAPSIBLE_HEADER_ICON_CLOSED);
            this.button.classList.remove("fa-caret-up");
            this.button.classList.add("fa-caret-down");
        }
    }
    get collapsed() {
        return this.slider.hasClass(COLLAPSIBLE_CLOSED);
    }
    set headerTitle(value) {
        this.header.node.innerText = value;
    }
}
exports.CollapsiblePanel = CollapsiblePanel;
//# sourceMappingURL=collapsiblepanel.js.map