// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
'use strict';

import {
  RenderMime
} from 'jupyterlab/lib/rendermime';

import {
  OutputWidget
} from 'jupyterlab/lib/notebook/output-area';


import {
  loadModeByMIME
} from 'jupyterlab/lib/codemirror';

import {
  Widget
} from 'phosphor-widget';

import 'codemirror/lib/codemirror.css';

import {
  DiffView, MergeView, MergeViewEditorConfiguration
} from './mergeview';

import {
  sanitize
} from 'sanitizer';

import {
  nbformat
} from 'jupyterlab/lib/notebook/notebook/nbformat';

import {
  valueIn
} from './util';

import {
  CellDiffModel, NotebookDiffModel, IDiffModel,
  IStringDiffModel, StringDiffModel, OutputDiffModel
} from './diffmodel';

const COLLAPISBLE_HEADER = 'jp-Collapsible-header';
const COLLAPISBLE_HEADER_ICON = 'jp-Collapsible-header-icon';
const COLLAPISBLE_HEADER_ICON_OPEN = 'jp-Collapsible-header-icon-opened';
const COLLAPISBLE_HEADER_ICON_CLOSED = 'jp-Collapsible-header-icon-closed';
const COLLAPISBLE_SLIDER = 'jp-Collapsible-slider';
const COLLAPSIBLE_OPEN = 'jp-Collapsible-opened';
const COLLAPSIBLE_CLOSED = 'jp-Collapsible-closed';
const COLLAPSIBLE_CONTAINER = 'jp-Collapsible-container';


/**
 * A list of outputs considered safe.
 */
const safeOutputs = ['text/plain', 'text/latex', 'image/png', 'image/jpeg',
                    'application/vnd.jupyter.console-text'];

/**
 * A list of outputs that are sanitizable.
 */
const sanitizable = ['text/svg', 'text/html'];

/**
 * A list of MIME types that can be shown as string diff.
 */
const stringDiffMimeTypes = ['text/html', 'text/plain'];


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


/**
 * A wrapper view for showing StringDiffModels in a MergeView
 */
class NbdimeMergeView extends Widget {
  constructor(remote: IStringDiffModel, editorClasses: string[],
              local?: IStringDiffModel, merged?: any) {
    super();
    let opts: MergeViewEditorConfiguration = {remote: remote};
    opts.collapseIdentical = true;
    opts.local = local ? local : null;
    //opts.merged = merged ? merged : null;
    this._mergeview = new MergeView(this.node, opts);
    this._editors = [];
    if (this._mergeview.left) {
      this._editors.push(this._mergeview.left);
    }
    if (this._mergeview.right) {
      this._editors.push(this._mergeview.right);
    }
    if (this._mergeview.merge) {
      this._editors.push(this._mergeview.merge);
    }
        
    if (remote.mimetype) {
      // Set the editor mode to the MIME type.
      for (let e of this._editors) {
        loadModeByMIME(e.orig, remote.mimetype);
      }
      loadModeByMIME(this._mergeview.base, remote.mimetype);
    }
  }
  
  protected _mergeview: MergeView;
  protected _editors: DiffView[];
}


/**
 * Widget for outputs with renderable MIME data.
 */
class RenderableView extends Widget {
  constructor(model: OutputDiffModel, editorClass: string[],
              rendermime: RenderMime<Widget>) {
    super();
    this._rendermime = rendermime;
    let bdata = model.base as nbformat.IOutput;
    let rdata = model.remote as nbformat.IOutput;
    this.layout = new PanelLayout();

    let ci = 0;
    if (bdata){
      let widget = this.createOutput(bdata, false);
      (this.layout as PanelLayout).addChild(widget);
      widget.addClass(editorClass[ci++]);
    }
    if (rdata && rdata !== bdata) {
      let widget = this.createOutput(rdata, false);
      (this.layout as PanelLayout).addChild(widget);
      widget.addClass(editorClass[ci++]);
    }
  }

  /**
   * Checks if all MIME types of a MIME bundle are safe or can be sanitized.
   */
  static safeOrSanitizable(bundle: nbformat.MimeBundle) {
    let keys = Object.keys(bundle);
    for (let key of keys) {
      if (valueIn(key, safeOutputs)) {
        continue;
      } else if (valueIn(key, sanitizable)) {
        let out = bundle[key];
        if (typeof out === 'string') {
          continue;
        } else {
          return false;
        }
      } else {
        return false;
      }
    }
    return true;
  }

  /**
   * Checks if a cell output can be rendered as untrusted (either safe or
   * sanitizable)
   */
  static canRenderUntrusted(model: OutputDiffModel): boolean {
    let toTest: nbformat.IOutput[] = [];
    if (model.base) {
      toTest.push(model.base);
    }
    if (model.remote && model.remote !== model.base) {
      toTest.push(model.remote);
    }
    for (let o of toTest) {
      if (valueIn(o.output_type, ['execute_result', 'display_data'])) {
        let bundle = (o as any).data as nbformat.MimeBundle;
        if (!this.safeOrSanitizable(bundle)) {
          return false;
        }
      } else if (valueIn(o.output_type, ['stream', 'error'])) {
        // Unknown output type
        return false;
      }
    }
    return true;
  }

  /**
   * Create a widget which renders the given cell output
   */
  protected createOutput(output: nbformat.IOutput, trusted: boolean): Widget {
    let widget = new OutputWidget({rendermime: this._rendermime});
    widget.render(output, trusted);
    return widget;
  }

  _sanitized: boolean;
  _rendermime: RenderMime<Widget>;
}
  