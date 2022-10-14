// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
'use strict';
Object.defineProperty(exports, "__esModule", { value: true });
exports.RenderableOutputView = exports.OutputPanel = void 0;
const widgets_1 = require("@lumino/widgets");
const algorithm_1 = require("@lumino/algorithm");
const rendermime_1 = require("@jupyterlab/rendermime");
const collapsiblepanel_1 = require("../../common/collapsiblepanel");
const mergeview_1 = require("../../common/mergeview");
const util_1 = require("../../common/util");
const common_1 = require("./common");
const renderable_1 = require("./renderable");
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
let _base64 = /^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$/;
function isBase64(data, minLength = 64) {
    return data !== null && data.length > minLength && _base64.test(data.replace('\n', ''));
}
/**
 * A panel responsible for rendering an output diff
 */
class OutputPanel extends widgets_1.Panel {
    /**
     *
     */
    constructor(model, parentModel, editorClasses, rendermime) {
        super();
        this._mimetype = null;
        this.forceText = false;
        this.model = model;
        this.rendermime = rendermime;
        this.editorClasses = editorClasses;
        model.trustedChanged.connect((sender, trusted) => {
            this.trustedChanged(trusted);
        });
        if (OutputPanel.isTrustSignificant(model, this.rendermime)) {
            this.addClass(UNTRUSTED_CLASS);
        }
        if (model.added) {
            if (!parentModel.added) {
                // Implies this is added output
                let addSpacer = new widgets_1.Widget();
                addSpacer.node.textContent = 'Output added';
                addSpacer.addClass(common_1.ADD_DEL_LABEL_CLASS);
                this.addWidget(addSpacer);
            }
            this.addClass(common_1.ADDED_DIFF_CLASS);
        }
        else if (model.deleted) {
            if (!parentModel.deleted) {
                // Implies this is deleted output
                let delSpacer = new widgets_1.Widget();
                delSpacer.node.textContent = 'Output deleted';
                delSpacer.addClass(common_1.ADD_DEL_LABEL_CLASS);
                this.addWidget(delSpacer);
            }
            this.addClass(common_1.DELETED_DIFF_CLASS);
        }
        else if (model.unchanged) {
            this.addClass(common_1.UNCHANGED_DIFF_CLASS);
        }
        else {
            this.addClass(common_1.TWOWAY_DIFF_CLASS);
        }
        let view = this.createView();
        this.initContainer(view);
        this.createHoverMenu();
        this.addClass(OUTPUT_PANEL_CLASS);
    }
    /**
     * Add view to panel, possibly wrapped
     */
    initContainer(view) {
        if (this.model.collapsible) {
            this.container = new collapsiblepanel_1.CollapsiblePanel(view, this.model.collapsibleHeader, this.model.startCollapsed);
        }
        else {
            this.container = this;
            this.container.addWidget(view);
        }
        this.view = view;
    }
    /**
     * Replace a view with a new one
     */
    replaceView(view) {
        let old = this.view;
        let i = this.container.widgets.indexOf(old);
        this.container.insertWidget(i, view);
        old.parent = null;
        this.view = view;
    }
    /**
     * Create a text or rendered view of the output diff model
     */
    createView(forceText = false) {
        let view = null;
        let model = this.model;
        let rendermime = this.rendermime;
        // Take one of three actions, depending on output types
        // 1) Renderable types: Side-by-side comparison.
        // 2) Text-type output: Show a MergeView with text diff.
        // 3) Unknown types: Stringified JSON diff.
        let renderable = RenderableOutputView.canRender(model, rendermime);
        if (renderable && !forceText) {
            // 1.
            let rov = new RenderableOutputView(model, this.editorClasses, rendermime, this.selectedMimetype);
            view = rov;
        }
        else {
            // 2. or 3.
            view = this.createOutputTextView();
        }
        return view;
    }
    /**
     * Create text view of output
     */
    createOutputTextView() {
        // Take one of three actions, depending on output types
        // 1) N/A here, see method createView above
        // 2) Known, non-binary MIME: Show a MergeView with text diff.
        // 3) Unknown types: Stringified JSON diff.
        let view;
        let model = this.model;
        // Find highest order MIME-type supported by rendermime
        let key = null;
        if (this.selectedMimetype === null) {
            algorithm_1.find(this.rendermime.mimeTypes, (mt) => {
                key = model.hasMimeType(mt);
                return key !== null;
            });
        }
        else {
            key = model.hasMimeType(this.selectedMimetype);
        }
        if (key) {
            let stringModel = model.stringify(key);
            let aValue = stringModel.base || stringModel.remote;
            if (!isBase64(aValue)) {
                // 2.
                view = mergeview_1.createNbdimeMergeView(stringModel);
            }
        }
        if (!view) {
            // 3.
            view = mergeview_1.createNbdimeMergeView(model.stringify());
        }
        return view;
    }
    /**
     * Creates a menu that is shown when hovering over the output.
     *
     * Stored in this.menu.
     */
    createHoverMenu() {
        this.menu = new widgets_1.Panel();
        this.menu.addClass(HOVER_MENU_CLASS);
        this.container.addWidget(this.menu);
        // Add rendered/source toggle:
        let btnSource = document.createElement('button');
        let sourceText = ['Show source', 'Render'];
        btnSource.innerText = sourceText[0];
        btnSource.onclick = (ev) => {
            this.forceText = !this.forceText;
            btnSource.innerText = sourceText[this.forceText ? 1 : 0];
            this.updateView();
        };
        let w = new widgets_1.Widget({ node: btnSource });
        w.addClass(SOURCE_BUTTON_CLASS);
        this.menu.addWidget(w);
        // Add trust button:
        let btnTrust = document.createElement('button');
        btnTrust.innerText = 'Trust';
        btnTrust.onclick = (ev) => {
            // Triggers change event:
            this.model.trusted = !this.model.trusted;
        };
        w = new widgets_1.Widget({ node: btnTrust });
        w.addClass(TRUST_BUTTON_CLASS);
        this.menu.addWidget(w);
        // Add mimetype select:
        let mimetypes = [];
        for (let output of this.model.contents) {
            let bundle = rendermime_1.OutputModel.getData(output);
            mimetypes = mimetypes.concat(Object.keys(bundle));
        }
        mimetypes = mimetypes.filter(util_1.unique);
        if (mimetypes.length > 1) {
            let cboMimetype = util_1.buildSelect(mimetypes);
            let selectedMimetype = this.selectedMimetype;
            if (selectedMimetype) {
                cboMimetype.selectedIndex = mimetypes.indexOf(selectedMimetype);
            }
            cboMimetype.onchange = (ev) => {
                this.selectedMimetype = mimetypes[cboMimetype.selectedIndex];
            };
            w = new widgets_1.Widget({ node: cboMimetype });
            w.addClass(MIMETYPE_SELECT_CLASS);
            this.menu.addWidget(w);
        }
        else if (mimetypes.length === 1) {
            let mtLabel = document.createElement('span');
            mtLabel.innerText = mimetypes[0];
            w = new widgets_1.Widget({ node: mtLabel });
            // w.addClass(MIMETYPE_SELECT_CLASS);
            this.menu.addWidget(w);
        }
    }
    /**
     * Update trusted status
     */
    trustedChanged(trusted) {
        this.updateView();
        if (trusted) {
            this.removeClass(UNTRUSTED_CLASS);
        }
        else if (OutputPanel.isTrustSignificant(this.model, this.rendermime)) {
            this.addClass(UNTRUSTED_CLASS);
        }
    }
    /**
     * Update view
     */
    updateView() {
        let model = this.model;
        if (this.view instanceof RenderableOutputView) {
            // Previosuly rendered
            if (!this.forceText && RenderableOutputView.canRender(model, this.rendermime)) {
                // Can still render
                this.view.updateView(this.selectedMimetype, model.trusted);
            }
            else {
                // Can no longer render
                let view = this.createView(this.forceText);
                this.replaceView(view);
            }
        }
        else {
            // Previously text output
            // Here, we replace the view irregardles of old vs new type
            let view = this.createView(this.forceText);
            this.replaceView(view);
        }
    }
    get selectedMimetype() {
        if (this._mimetype !== null) {
            return this._mimetype;
        }
        let data = rendermime_1.OutputModel.getData(this.model.base || this.model.remote);
        let mt = this.rendermime.preferredMimeType(data, this.model.trusted ? 'any' : 'ensure');
        return mt === undefined ? null : mt;
    }
    set selectedMimetype(value) {
        if (this._mimetype !== value) {
            this._mimetype = value;
            this.updateView();
        }
    }
    /**
     * Whether trust can affect the output rendering.
     */
    static isTrustSignificant(model, rendermime) {
        if (model.trusted) {
            return false;
        }
        let toTest = [];
        if (model.base) {
            toTest.push(model.base);
        }
        if (model.remote && model.remote !== model.base) {
            toTest.push(model.remote);
        }
        for (let o of toTest) {
            let untrustedModel = new rendermime_1.OutputModel({ value: o, trusted: false });
            let modelMimeTypes = Object.keys(untrustedModel.data);
            let rendererMimeTypes = algorithm_1.toArray(rendermime.mimeTypes);
            let candidates = util_1.intersection(modelMimeTypes, rendererMimeTypes);
            for (let mimeType of candidates) {
                let factory = rendermime.getFactory(mimeType);
                if (factory && (!factory.safe || sanitizable.indexOf(mimeType) !== -1)) {
                    return true;
                }
            }
        }
        return false;
    }
}
exports.OutputPanel = OutputPanel;
/**
 * Widget for an output with renderable MIME data.
 */
class RenderableOutputView extends renderable_1.RenderableDiffView {
    constructor(model, editorClass, rendermime, mimetype) {
        super(model, editorClass, rendermime, mimetype);
    }
    /**
     * Create a widget which renders the given cell output
     */
    createSubView(output, trusted) {
        let panel = new RenderedOutputWidget(this.rendermime);
        panel.updateView(output, trusted, this.mimetype);
        return panel;
    }
    /**
     * Update trusted status
     */
    updateView(mimeType, trusted) {
        let i = 0;
        let model = this.model;
        this.mimetype = mimeType;
        algorithm_1.each(this.layout.widgets, (w) => {
            if (w instanceof RenderedOutputWidget) {
                let output = null;
                if (i === 0 && model.base) {
                    // Use base data
                    output = model.base;
                }
                else if (model.remote) {
                    output = model.remote;
                }
                if (output) {
                    w.updateView(output, trusted, mimeType);
                }
                ++i;
            }
        });
    }
    /**
     * Checks if a cell output can be rendered (either safe/trusted or
     * sanitizable)
     */
    static canRender(model, rendermime) {
        let toTest = model.contents;
        for (let o of toTest) {
            let bundle = rendermime_1.OutputModel.getData(o);
            let mimetype = rendermime.preferredMimeType(bundle, model.trusted ? 'any' : 'ensure');
            if (!mimetype) {
                return false;
            }
        }
        return true;
    }
}
exports.RenderableOutputView = RenderableOutputView;
class RenderedOutputWidget extends widgets_1.Panel {
    /**
     *
     */
    constructor(rendermime) {
        super();
        this.rendermime = rendermime;
    }
    updateView(output, trusted, mimetype) {
        let old = this.renderer;
        this.renderer = this.createRenderer(output, trusted, mimetype);
        if (old !== undefined) {
            old.dispose();
        }
        this.addWidget(this.renderer);
    }
    createRenderer(output, trusted, mimetype) {
        let model = new rendermime_1.OutputModel({ value: output, trusted });
        let widget = this.rendermime.createRenderer(mimetype);
        widget.renderModel(model);
        widget.addClass(RENDERED_OUTPUT_CLASS);
        let bundle = rendermime_1.OutputModel.getData(output);
        if (isBase64(bundle[mimetype])) {
            widget.addClass(DATA_IS_BASE64_CLASS);
        }
        return widget;
    }
}
//# sourceMappingURL=output.js.map