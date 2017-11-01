// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.

'use strict';


import {
  Widget
} from '@phosphor/widgets';

import {
  CodeEditorWrapper, CodeEditor
} from '@jupyterlab/codeeditor';

import {
  CodeMirrorEditorFactory, CodeMirrorEditor
} from '@jupyterlab/codemirror';


export
class EditorWidget extends CodeEditorWrapper {
  /**
   * Store all editor instances for operations that
   * need to loop over all instances.
   */
  constructor(value?: string, options?: Partial<CodeMirrorEditor.IConfig>) {
    super({
      model: new CodeEditor.Model({value}),
      factory: function() {
        let factory = new CodeMirrorEditorFactory(options);
        return factory.newInlineEditor.bind(factory);
      }()
    });
    EditorWidget.editors.push(this.cm);
  }

  public static editors: CodeMirror.Editor[] = [];

  get cm(): CodeMirror.Editor {
    return (this.editor as CodeMirrorEditor).editor;
  }

  get doc(): CodeMirror.Doc {
    return (this.editor as CodeMirrorEditor).doc;
  }

  /**
   * A message handler invoked on an `'resize'` message.
   */
  protected onResize(msg: Widget.ResizeMessage): void {
    if (!this.staticLoaded) {
      if (msg.width < 0 || msg.height < 0) {
        this.cm.setSize(null, null);
      } else {
        super.onResize(msg);
      }
      if (this.editor.getOption('readOnly') && document.contains(this.node)) {
        this.staticLoaded = true;
      }
    }
  }

  staticLoaded = false;
}
