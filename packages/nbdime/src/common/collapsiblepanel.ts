// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
'use strict';

import { Widget, Panel } from '@lumino/widgets';

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
export class CollapsiblePanel extends Panel {
  static createHeader(headerTitle?: string): Panel {
    let header = new Panel();
    header.addClass(COLLAPSIBLE_HEADER);
    if (headerTitle) {
      header.node.textContent = headerTitle;
    }
    let button = document.createElement('button');
    button.className = COLLAPSIBLE_HEADER_ICON;
    header.node.appendChild(button);

    return header;
  }

  constructor(inner: Widget, headerTitle?: string, collapsed?: boolean) {
    super();
    this.addClass(COLLAPSIBLE_CLASS);
    this.inner = inner;
    let header = CollapsiblePanel.createHeader(headerTitle);
    this.header = header;
    this.button = header.node.getElementsByClassName(
      COLLAPSIBLE_HEADER_ICON,
    )[0] as HTMLElement;
    header.node.onclick = this.toggleCollapsed.bind(this);
    this.addWidget(header);
    this.container = new Panel();
    this.container.addClass(COLLAPSIBLE_CONTAINER);
    this.slider = new Panel();
    this.slider.addClass(COLLAPSIBLE_SLIDER);
    this.slider.addWidget(inner);
    this.container.addWidget(this.slider);
    this.addWidget(this.container);

    this.slider.addClass(
      collapsed === true ? COLLAPSIBLE_CLOSED : COLLAPSIBLE_OPEN,
    );
    this.button.classList.add(
      collapsed === true
        ? COLLAPSIBLE_HEADER_ICON_CLOSED
        : COLLAPSIBLE_HEADER_ICON_OPEN,
    );
    this.button.classList.add('fa');
    this.button.classList.add(
      collapsed === true ? 'fa-caret-down' : 'fa-caret-up',
    );
  }

  toggleCollapsed(): void {
    let slider = this.slider;
    let button = this.button;
    if (this.collapsed) {
      slider.removeClass(COLLAPSIBLE_CLOSED);
      slider.addClass(COLLAPSIBLE_OPEN);
      button.classList.remove(COLLAPSIBLE_HEADER_ICON_CLOSED);
      button.classList.add(COLLAPSIBLE_HEADER_ICON_OPEN);
      this.button.classList.remove('fa-caret-down');
      this.button.classList.add('fa-caret-up');
    } else {
      slider.removeClass(COLLAPSIBLE_OPEN);
      slider.addClass(COLLAPSIBLE_CLOSED);
      button.classList.remove(COLLAPSIBLE_HEADER_ICON_OPEN);
      button.classList.add(COLLAPSIBLE_HEADER_ICON_CLOSED);
      this.button.classList.remove('fa-caret-up');
      this.button.classList.add('fa-caret-down');
    }
  }

  get collapsed(): boolean {
    return this.slider.hasClass(COLLAPSIBLE_CLOSED);
  }

  set headerTitle(value: string) {
    this.header.node.innerText = value;
  }

  inner: Widget;

  header: Panel;
  slider: Panel;
  container: Panel;
  button: HTMLElement;
}
