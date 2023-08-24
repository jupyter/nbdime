// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.

'use strict';

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

import { type EditorView } from '@codemirror/view';
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
    )) {
      if (extensionFactory.name === 'lineNumbers') {
        extensions.addExtension(extensionFactory);
      }
      if (extensionFactory.name === 'readOnly') {
        extensions.addExtension(extensionFactory);
      }
      if (extensionFactory.name === 'theme') {
        extensions.addExtension(extensionFactory)
      }
      if (extensionFactory.name === 'allowMultipleSelections') {
        extensions.addExtension(extensionFactory);
      }
      if (extensionFactory.name === 'tabSize') {
        extensions.addExtension(extensionFactory);
      }
    }

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

  const model =  new CodeEditor.Model({sharedModel});

  super({
    model: model,
    editorOptions: {config: {lineNumbers: true}},
    factory: function() {
      let factory = new CodeMirrorEditorFactory({
        extensions,
        languages
      });

    return factory.newInlineEditor.bind(factory);
    }()
  });
    this.staticLoaded = false;
  }

  get cm(): EditorView {
    return (this.editor as CodeMirrorEditor).editor;
  }

  get doc(): Text {
    return (this.editor as CodeMirrorEditor).doc;
  }

  readonly editor: CodeMirrorEditor;
  staticLoaded: boolean;
}
