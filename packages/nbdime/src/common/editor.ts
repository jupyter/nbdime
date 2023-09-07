// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.

'use strict';

import { StreamLanguage } from '@codemirror/language';

import { type EditorView } from '@codemirror/view';

import type { Text } from '@codemirror/state';

import { YFile, IYText } from '@jupyter/ydoc';

import {
  CodeEditorWrapper, CodeEditor
} from '@jupyterlab/codeeditor';

import {
  CodeMirrorEditorFactory,
  CodeMirrorEditor,
  EditorExtensionRegistry,
  EditorLanguageRegistry,
  EditorThemeRegistry,
  parseMathIPython,
  ybinding
} from '@jupyterlab/codemirror';

export interface IEditorWidgetOptions extends Omit<CodeMirrorEditor.IOptions, 'host' | 'model' | 'inline'> {
  /**
   * The starting value of the editor.
   */
  value?: string

  /**
   * Editor configuration
   */
  config?: {
    /**
     * Whether CodeMirror should scroll or wrap for long lines. Defaults to false (scroll).
     */
    lineWrap?: boolean;

    /**
     * Whether to show line numbers to the left of the editor.
     */
    lineNumbers?: boolean;

    /** 
     * This disables editing of the editor content by the user.
     * If the special value "nocursor" is given (instead of simply true), focusing of the editor is also disallowed.
     */
    readOnly?: boolean | string;
  }
}


export
class EditorWidget extends CodeEditorWrapper {
  /**
   * Store all editor instances for operations that
   * need to loop over all instances.
   */
  constructor(value?: string, options?: IEditorWidgetOptions) {
    const sharedModel = new YFile();
    if (value) {
      sharedModel.source = value
    }

    const languages = options?.languages ?? createLanguagesRegistry();
    const extensions = options?.extensionsRegistry ?? createExtensionsRegistry(createThemeRegistry());

    const model =  new CodeEditor.Model({sharedModel});

    super({
      model: model,
      editorOptions: options,
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

export function createExtensionsRegistry(themes: EditorThemeRegistry): EditorExtensionRegistry {
  const extensions = new EditorExtensionRegistry();

  // Register default extensions
  const extensionNameList = ['lineNumbers', 'readOnly', 'theme', 'allowMultipleSelections', 'tabSize'];
  for (const extensionFactory of EditorExtensionRegistry.getDefaultExtensions(
    {
      themes
    }
  )) {
    for (const extensionName of extensionNameList) {
      if (extensionFactory.name === extensionName) {
        extensions.addExtension(extensionFactory);
      }
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
  return extensions;
}

export function createLanguagesRegistry(): EditorLanguageRegistry {
  const languages = new EditorLanguageRegistry();

  // Register default languages
  for (const language of EditorLanguageRegistry.getDefaultLanguages()) { languages.addLanguage(language); }

  // Add Jupyter Markdown flavor here to support
  // code block highlighting.
  languages.addLanguage({
    name: 'ipythongfm',
    mime: 'text/x-ipythongfm',
    load: async () => {
      const [m, tex] = await Promise.all([
        import('@codemirror/lang-markdown'),
        import('@codemirror/legacy-modes/mode/stex')
      ]);
      return m.markdown({
        base: m.markdownLanguage,
        codeLanguages: (info: string) => languages.findBest(info) as any,
        extensions: [
          parseMathIPython(StreamLanguage.define(tex.stexMath).parser)
        ]
      });
    }
  });

  return languages;
}

export function createThemeRegistry(): EditorThemeRegistry {
  const themes = new EditorThemeRegistry();

  for (const theme of EditorThemeRegistry.getDefaultThemes()) { themes.addTheme(theme); }
  return themes;
}
