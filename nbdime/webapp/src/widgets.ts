// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
'use strict';

import {
  Widget
} from 'phosphor-widget';

const COLLAPISBLE_HEADER = 'jp-Collapsible-header';
const COLLAPISBLE_HEADER_ICON = 'jp-Collapsible-header-icon';
const COLLAPISBLE_HEADER_ICON_OPEN = 'jp-Collapsible-header-icon-opened';
const COLLAPISBLE_HEADER_ICON_CLOSED = 'jp-Collapsible-header-icon-closed';
const COLLAPISBLE_SLIDER = 'jp-Collapsible-slider';
const COLLAPSIBLE_OPEN = 'jp-Collapsible-opened';
const COLLAPSIBLE_CLOSED = 'jp-Collapsible-closed';
const COLLAPSIBLE_CONTAINER = 'jp-Collapsible-container';


/**
 * CollapsibleWidget
 */
class CollapsibleWidget extends Widget {
  static createHeader(headerTitle?: string): HTMLSpanElement {
    let header = document.createElement('div');
    header.className = COLLAPISBLE_HEADER;
    if (headerTitle) {
      //let title = document.createElement('span');
      header.innerText = headerTitle;
      //header.appendChild(title);
    }
    let button = document.createElement('span');
    button.className = COLLAPISBLE_HEADER_ICON;
    header.appendChild(button)
    
    return header;
  }
  
  constructor(public inner: Widget, headerTitle?: string, collapsed?: boolean) {
    super();
    let constructor = this.constructor as typeof CollapsibleWidget;
    let header = constructor.createHeader(headerTitle);
    this.button = header.getElementsByClassName(
      COLLAPISBLE_HEADER_ICON)[0] as HTMLElement;
    header.onclick = this.toggleCollapsed.bind(this);
    this.node.appendChild(header);
    this.container = document.createElement('div');
    this.container.className = COLLAPSIBLE_CONTAINER;
    this.slider = document.createElement('div');
    this.slider.classList.add(COLLAPISBLE_SLIDER);
    this.slider.appendChild(inner.node)
    this.container.appendChild(this.slider);
    this.node.appendChild(this.container);
    
    this.slider.classList.add(
      collapsed === true ? 
      COLLAPSIBLE_CLOSED : 
      COLLAPSIBLE_OPEN);
    this.button.classList.add(
      collapsed === true ? 
      COLLAPISBLE_HEADER_ICON_CLOSED : 
      COLLAPISBLE_HEADER_ICON_OPEN);
  }
  
  toggleCollapsed(): void {
    let slider = this.slider;
    let button = this.button;
    if (this.collapsed) {
      slider.classList.remove(COLLAPSIBLE_CLOSED);
      slider.classList.add(COLLAPSIBLE_OPEN);
      button.classList.remove(COLLAPISBLE_HEADER_ICON_CLOSED);
      button.classList.add(COLLAPISBLE_HEADER_ICON_OPEN);
        
    } else {
      slider.classList.remove(COLLAPSIBLE_OPEN);
      slider.classList.add(COLLAPSIBLE_CLOSED);
      button.classList.remove(COLLAPISBLE_HEADER_ICON_OPEN);
      button.classList.add(COLLAPISBLE_HEADER_ICON_CLOSED);
    }
  }
  
  get collapsed(): boolean {
    return this.slider.classList.contains(COLLAPSIBLE_CLOSED);
  }
  
  slider: HTMLElement;
  container: HTMLElement;
  button: HTMLElement;
}
