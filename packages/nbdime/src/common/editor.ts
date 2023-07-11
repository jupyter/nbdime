// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.

'use strict';

import type { Widget } from '@lumino/widgets';

/* import type {
  Widget
} from '@lumino/widgets'; */

import {
  CodeEditorWrapper, CodeEditor
} from '@jupyterlab/codeeditor';

import {
  CodeMirrorEditorFactory,
  CodeMirrorEditor,
  EditorExtensionRegistry,
  EditorLanguageRegistry,
  EditorThemeRegistry,
  ybinding
} from '@jupyterlab/codemirror';

//import { ITranslator, nullTranslator } from '@jupyterlab/translation';

import type { EditorView } from '@codemirror/view';
import type { Text } from '@codemirror/state';
import { YFile, IYText } from '@jupyter/ydoc';

export
class EditorWidget extends CodeEditorWrapper {
  /**
   * Store all editor instances for operations that
   * need to loop over all instances.
   */

constructor(value?: string, options?: CodeMirrorEditor.IOptions) {
  const sharedModel = new YFile();
  if (value) {
    sharedModel.source = value
  }

  const extensions = new EditorExtensionRegistry();
  const languages = new EditorLanguageRegistry();
  const registry = new EditorExtensionRegistry();
  const themes = new EditorThemeRegistry();


  for (const theme of EditorThemeRegistry.getDefaultThemes(
    )) { themes.addTheme(theme);}


  // Register default languages
  for (const language of EditorLanguageRegistry.getDefaultLanguages(
  )) {languages.addLanguage(language);}

  // Register default extensions
  for (const extensionFactory of EditorExtensionRegistry.getDefaultExtensions(
    {
      themes
    }
    )) {registry.addExtension(extensionFactory);}


    extensions.addExtension({
      name: 'shared-model-binding',
      factory: options => {
        const sharedModel = options.model.sharedModel as IYText;
        return EditorExtensionRegistry.createImmutableExtension(
          ybinding({
            ytext: sharedModel.ysource,
            undoManager: sharedModel.undoManager ?? undefined
          })
        );
      }
    });


  /*console.log('themes:', themes);
  console.log('languages:', languages);
  console.log('extensions:', extensions);*/
  const model =  new CodeEditor.Model({sharedModel});
  model.mimeType = 'text/x-python'


  super({
    model: model,
    factory: function() {
      let factory = new CodeMirrorEditorFactory({
        extensions,
        languages
      });

    return factory.newInlineEditor.bind(factory);
    }()
  });

    /********************WORKING VERSION ****************** */
    /*constructor(value?: string, options?: CodeMirrorEditor.IOptions) {
      /*if (options && options.readOnly) {
        // Prevent readonly editor from trapping tabs
        options.extraKeys = {Tab: false, 'Shift-Tab': false};
      }*/
      /*const sharedModel = new YFile();
      if (value) {
        sharedModel.source = value
      }
      super({
        model: new CodeEditor.Model({sharedModel}),
        factory: function() {
          let factory = new CodeMirrorEditorFactory(/*options*/ /*);*/
          /*return factory.newInlineEditor.bind(factory);
        }()
      });*/
    /********************************************************** */
    this.staticLoaded = false;
    //EditorWidget.editors.push(this.cm);
  }
 //public static editors: EditorView[] = [];

  get cm(): EditorView {
    return (this.editor as CodeMirrorEditor).editor;
  }

  get doc(): Text {
    return (this.editor as CodeMirrorEditor).doc;
  }

    readonly editor: CodeMirrorEditor;


  /**  FIX ME
   * A message handler invoked on an `'resize'` message.
   */
  /* protected onResize(msg: Widget.ResizeMessage): void {
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
  } */

  staticLoaded: boolean;
}
