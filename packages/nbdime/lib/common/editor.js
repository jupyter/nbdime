// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
'use strict';
Object.defineProperty(exports, "__esModule", { value: true });
exports.EditorWidget = void 0;
const codeeditor_1 = require("@jupyterlab/codeeditor");
const codemirror_1 = require("@jupyterlab/codemirror");
class EditorWidget extends codeeditor_1.CodeEditorWrapper {
    /**
     * Store all editor instances for operations that
     * need to loop over all instances.
     */
    constructor(value, options) {
        if (options && options.readOnly) {
            // Prevent readonly editor from trapping tabs
            options.extraKeys = { Tab: false, 'Shift-Tab': false };
        }
        super({
            model: new codeeditor_1.CodeEditor.Model({ value }),
            factory: function () {
                let factory = new codemirror_1.CodeMirrorEditorFactory(options);
                return factory.newInlineEditor.bind(factory);
            }()
        });
        this.staticLoaded = false;
        EditorWidget.editors.push(this.cm);
    }
    get cm() {
        return this.editor.editor;
    }
    get doc() {
        return this.editor.doc;
    }
    /**
     * A message handler invoked on an `'resize'` message.
     */
    onResize(msg) {
        if (!this.staticLoaded) {
            if (msg.width < 0 || msg.height < 0) {
                this.cm.setSize(null, null);
            }
            else {
                super.onResize(msg);
            }
            if (this.editor.getOption('readOnly') && document.contains(this.node)) {
                this.staticLoaded = true;
            }
        }
    }
}
exports.EditorWidget = EditorWidget;
EditorWidget.editors = [];
//# sourceMappingURL=editor.js.map