// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
'use strict';

import type * as nbformat from '@jupyterlab/nbformat';

import type { TranslationBundle } from '@jupyterlab/translation';

import { Panel, Widget } from '@lumino/widgets';

import { each, find, toArray } from '@lumino/algorithm';

import {
  IRenderMimeRegistry,
  OutputModel,
  IRenderMime,
} from '@jupyterlab/rendermime';

import { DiffPanel } from '../../common/basepanel';

import { CollapsiblePanel } from '../../common/collapsiblepanel';

import { createNbdimeMergeView } from '../../common/mergeview';

import { buildSelect, unique, intersection } from '../../common/util';

import type { ICellDiffViewOptions } from './cell';

import {
  ADDED_DIFF_CLASS,
  DELETED_DIFF_CLASS,
  TWOWAY_DIFF_CLASS,
  UNCHANGED_DIFF_CLASS,
  ADD_DEL_LABEL_CLASS,
} from './common';

import { RenderableDiffView } from './renderable';

import type { OutputDiffModel } from '../model';

/**
 * Class for output panel
 */
const OUTPUT_PANEL_CLASS = 'jp-Diff-outputPanel';

/**
 * Class for a single rendered output view
 */
const RENDERED_OUTPUT_CLASS = 'jp-Diff-renderedOutput';

/**
 * Output is untrusted, and can benefit from being trusted
 */
const UNTRUSTED_CLASS = 'jp-Diff-trustCandidate';

/**
 * Menu with actions for outputs
 */
const HOVER_MENU_CLASS = 'jp-Diff-outputMenu';

/**
 * Menu button to trust output content
 */
const TRUST_BUTTON_CLASS = 'jp-Diff-trustOutputButton';

/**
 * Menu button for showing output as text instead of rendered
 */
const SOURCE_BUTTON_CLASS = 'jp-Diff-showOutputSourceButton';

/**
 * Class for outputs which data is base64
 */
const DATA_IS_BASE64_CLASS = 'jp-diff-base64Output';

/**
 * Class of dropdown for selecting mimetype to show
 */

const MIMETYPE_SELECT_CLASS = 'jp-Diff-outputMimetypeSelect';

/**
 * A list of outputs that are sanitizable.
 */
const sanitizable = ['text/html'];

let _base64 =
  /^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$/;
function isBase64(data: string | null, minLength = 64): boolean {
  return (
    data !== null &&
    data.length > minLength &&
    _base64.test(data.replace('\n', ''))
  );
}

/**
 * A panel responsible for rendering an output diff
 */
export class OutputPanel extends DiffPanel<OutputDiffModel> {
  /**
   *
   */
  constructor({
    parent: parentModel,
    editorClasses,
    rendermime,
    ...others
  }: ICellDiffViewOptions<OutputDiffModel>) {
    super(others);
    this.rendermime = rendermime;
    this._trans = this._translator.load('nbdime');
    this.editorClasses = editorClasses;

    this._model.trustedChanged.connect(
      (sender: OutputDiffModel, trusted: boolean) => {
        this.trustedChanged(trusted);
      },
    );
    if (OutputPanel.isTrustSignificant(this._model, this.rendermime)) {
      this.addClass(UNTRUSTED_CLASS);
    }

    if (this._model.added) {
      if (!parentModel.added) {
        // Implies this is added output
        let addSpacer = new Widget();
        addSpacer.node.textContent = this._trans.__('Output added');
        addSpacer.addClass(ADD_DEL_LABEL_CLASS);
        this.addWidget(addSpacer);
      }
      this.addClass(ADDED_DIFF_CLASS);
    } else if (this._model.deleted) {
      if (!parentModel.deleted) {
        // Implies this is deleted output
        let delSpacer = new Widget();
        delSpacer.node.textContent = this._trans.__('Output deleted');
        delSpacer.addClass(ADD_DEL_LABEL_CLASS);
        this.addWidget(delSpacer);
      }
      this.addClass(DELETED_DIFF_CLASS);
    } else if (this._model.unchanged) {
      this.addClass(UNCHANGED_DIFF_CLASS);
    } else {
      this.addClass(TWOWAY_DIFF_CLASS);
    }

    let view = this.createView();
    this.initContainer(view);

    this.createHoverMenu();
    this.addClass(OUTPUT_PANEL_CLASS);
  }

  /**
   * Add view to panel, possibly wrapped
   */
  protected initContainer(view: Widget) {
    if (this._model.collapsible) {
      this.container = new CollapsiblePanel(
        view,
        this._model.collapsibleHeader,
        this._model.startCollapsed,
      );
    } else {
      this.container = this;
      this.container.addWidget(view);
    }
    this.view = view;
  }

  /**
   * Replace a view with a new one
   */
  protected replaceView(view: Widget) {
    let old = this.view;
    let i = this.container.widgets.indexOf(old);
    this.container.insertWidget(i, view);
    old.parent = null!;
    this.view = view;
  }

  /**
   * Create a text or rendered view of the output diff model
   */
  protected createView(forceText = false): Widget {
    let view: Widget | null = null;
    let model = this._model;
    let rendermime = this.rendermime;
    // Take one of three actions, depending on output types
    // 1) Renderable types: Side-by-side comparison.
    // 2) Text-type output: Show a MergeView with text diff.
    // 3) Unknown types: Stringified JSON diff.
    let renderable = RenderableOutputView.canRender(model, rendermime);
    if (renderable && !forceText) {
      // 1.
      let rov = new RenderableOutputView(
        model,
        this.editorClasses,
        rendermime,
        this.selectedMimetype!,
      );
      view = rov;
    } else {
      // 2. or 3.
      view = this.createOutputTextView();
    }
    return view;
  }

  /**
   * Create text view of output
   */
  protected createOutputTextView(): Widget {
    // Take one of three actions, depending on output types
    // 1) N/A here, see method createView above
    // 2) Known, non-binary MIME: Show a MergeView with text diff.
    // 3) Unknown types: Stringified JSON diff.
    let view: Widget | undefined;
    let model = this._model as OutputDiffModel;
    // Find highest order MIME-type supported by rendermime
    let key: string | string[] | null = null;
    if (this.selectedMimetype === null) {
      find(this.rendermime.mimeTypes, mt => {
        key = model.hasMimeType(mt);
        return key !== null;
      });
    } else {
      key = model.hasMimeType(this.selectedMimetype);
    }
    if (key) {
      let stringModel = model.stringify(key);
      let aValue = stringModel.base || stringModel.remote!;
      if (!isBase64(aValue)) {
        // 2.
        view = createNbdimeMergeView({
          remote: stringModel,
          factory: this._editorFactory,
          translator: this._translator,
          ...this._viewOptions,
        });
      }
    }
    if (!view) {
      // 3.
      view = createNbdimeMergeView({
        remote: model.stringify(),
        factory: this._editorFactory,
        translator: this._translator,
        ...this._viewOptions,
      });
    }
    return view;
  }

  /**
   * Creates a menu that is shown when hovering over the output.
   *
   * Stored in this.menu.
   */
  protected createHoverMenu() {
    this.menu = new Panel();
    this.menu.addClass(HOVER_MENU_CLASS);
    this.container.addWidget(this.menu);

    // Add rendered/source toggle:
    let btnSource = document.createElement('button');
    let sourceText = [this._trans.__('Show source'), this._trans.__('Render')];
    btnSource.textContent = sourceText[0];
    btnSource.onclick = (ev: MouseEvent) => {
      this.forceText = !this.forceText;
      btnSource.textContent = sourceText[this.forceText ? 1 : 0];
      this.updateView();
    };
    let w = new Widget({ node: btnSource });
    w.addClass(SOURCE_BUTTON_CLASS);
    this.menu.addWidget(w);

    // Add trust button:
    let btnTrust = document.createElement('button');
    btnTrust.textContent = this._trans.__('Trust');
    btnTrust.onclick = (ev: MouseEvent) => {
      // Triggers change event:
      this._model.trusted = !this._model.trusted;
    };
    w = new Widget({ node: btnTrust });
    w.addClass(TRUST_BUTTON_CLASS);
    this.menu.addWidget(w);

    // Add mimetype select:
    let mimetypes: string[] = [];
    for (let output of this._model.contents) {
      let bundle = OutputModel.getData(output);
      mimetypes = mimetypes.concat(Object.keys(bundle));
    }
    mimetypes = mimetypes.filter(unique);
    if (mimetypes.length > 1) {
      let cboMimetype = buildSelect(mimetypes);
      let selectedMimetype = this.selectedMimetype;
      if (selectedMimetype) {
        cboMimetype.selectedIndex = mimetypes.indexOf(selectedMimetype);
      }
      cboMimetype.onchange = (ev: Event) => {
        this.selectedMimetype = mimetypes[cboMimetype.selectedIndex];
      };
      w = new Widget({ node: cboMimetype });
      w.addClass(MIMETYPE_SELECT_CLASS);
      this.menu.addWidget(w);
    } else if (mimetypes.length === 1) {
      let mtLabel = document.createElement('span');
      mtLabel.innerText = mimetypes[0];
      w = new Widget({ node: mtLabel });
      // w.addClass(MIMETYPE_SELECT_CLASS);
      this.menu.addWidget(w);
    }
  }

  /**
   * Update trusted status
   */
  protected trustedChanged(trusted: boolean) {
    this.updateView();
    if (trusted) {
      this.removeClass(UNTRUSTED_CLASS);
    } else if (OutputPanel.isTrustSignificant(this._model, this.rendermime)) {
      this.addClass(UNTRUSTED_CLASS);
    }
  }

  /**
   * Update view
   */
  protected updateView(): void {
    let model = this._model;
    if (this.view instanceof RenderableOutputView) {
      // Previosuly rendered
      if (
        !this.forceText &&
        RenderableOutputView.canRender(model, this.rendermime)
      ) {
        // Can still render
        this.view.updateView(this.selectedMimetype!, model.trusted);
      } else {
        // Can no longer render
        let view = this.createView(this.forceText);
        this.replaceView(view);
      }
    } else {
      // Previously text output
      // Here, we replace the view irregardles of old vs new type
      let view = this.createView(this.forceText);
      this.replaceView(view);
    }
  }

  protected get selectedMimetype(): string | null {
    if (this._mimetype !== null) {
      return this._mimetype;
    }
    let data = OutputModel.getData(this._model.base || this._model.remote!);
    let mt = this.rendermime.preferredMimeType(
      data,
      this._model.trusted ? 'any' : 'ensure',
    );
    return mt === undefined ? null : mt;
  }

  protected set selectedMimetype(value: string | null) {
    if (this._mimetype !== value) {
      this._mimetype = value;
      this.updateView();
    }
  }

  protected rendermime: IRenderMimeRegistry;
  protected editorClasses: string[];
  protected container: Panel;

  protected view: Widget;

  protected menu: Panel;
  protected _mimetype: string | null = null;
  protected _trans: TranslationBundle;
  protected forceText = false;

  /**
   * Whether trust can affect the output rendering.
   */
  static isTrustSignificant(
    model: OutputDiffModel,
    rendermime: IRenderMimeRegistry,
  ): boolean {
    if (model.trusted) {
      return false;
    }
    let toTest: nbformat.IOutput[] = [];
    if (model.base) {
      toTest.push(model.base);
    }
    if (model.remote && model.remote !== model.base) {
      toTest.push(model.remote);
    }
    for (let o of toTest) {
      let untrustedModel = new OutputModel({ value: o, trusted: false });
      let modelMimeTypes = Object.keys(untrustedModel.data);
      let rendererMimeTypes = toArray(rendermime.mimeTypes);
      let candidates = intersection(modelMimeTypes, rendererMimeTypes);
      for (let mimeType of candidates) {
        let factory = rendermime.getFactory(mimeType);
        if (
          factory &&
          (!factory.safe || sanitizable.indexOf(mimeType) !== -1)
        ) {
          return true;
        }
      }
    }
    return false;
  }
}

/**
 * Widget for an output with renderable MIME data.
 */
export class RenderableOutputView extends RenderableDiffView<nbformat.IOutput> {
  constructor(
    model: OutputDiffModel,
    editorClass: string[],
    rendermime: IRenderMimeRegistry,
    mimetype: string,
  ) {
    super(model, editorClass, rendermime, mimetype);
  }

  /**
   * Create a widget which renders the given cell output
   */
  protected createSubView(output: nbformat.IOutput, trusted: boolean): Widget {
    let panel = new RenderedOutputWidget(this.rendermime);
    panel.updateView(output, trusted, this.mimetype);
    return panel;
  }

  /**
   * Update trusted status
   */
  updateView(mimeType: string, trusted: boolean): void {
    let i = 0;
    let model = this.model;
    this.mimetype = mimeType;
    each(this.layout!.widgets, (w: Widget) => {
      if (w instanceof RenderedOutputWidget) {
        let output: nbformat.IOutput | null = null;
        if (i === 0 && model.base) {
          // Use base data
          output = model.base;
        } else if (model.remote) {
          output = model.remote;
        }
        if (output) {
          w.updateView(output, trusted, mimeType);
        }
        ++i;
      }
    });
  }

  protected declare model: OutputDiffModel;

  /**
   * Checks if a cell output can be rendered (either safe/trusted or
   * sanitizable)
   */
  static canRender(
    model: OutputDiffModel,
    rendermime: IRenderMimeRegistry,
  ): boolean {
    let toTest = model.contents;
    for (let o of toTest) {
      let bundle = OutputModel.getData(o);
      let mimetype = rendermime.preferredMimeType(
        bundle,
        model.trusted ? 'any' : 'ensure',
      );
      if (!mimetype) {
        return false;
      }
    }
    return true;
  }
}

class RenderedOutputWidget extends Panel {
  /**
   *
   */
  constructor(rendermime: IRenderMimeRegistry) {
    super();
    this.rendermime = rendermime;
  }

  updateView(output: nbformat.IOutput, trusted: boolean, mimetype: string) {
    let old = this.renderer;
    this.renderer = this.createRenderer(output, trusted, mimetype);
    if (old !== undefined) {
      old.dispose();
    }
    this.addWidget(this.renderer);
  }

  protected createRenderer(
    output: nbformat.IOutput,
    trusted: boolean,
    mimetype: string,
  ): IRenderMime.IRenderer {
    let model = new OutputModel({ value: output, trusted });
    let widget = this.rendermime.createRenderer(mimetype);
    widget.renderModel(model);
    widget.addClass(RENDERED_OUTPUT_CLASS);
    let bundle = OutputModel.getData(output);
    if (isBase64(bundle[mimetype] as string)) {
      widget.addClass(DATA_IS_BASE64_CLASS);
    }
    return widget;
  }

  protected renderer: IRenderMime.IRenderer | undefined;

  protected rendermime: IRenderMimeRegistry;
}
