import { IEditorExtensionRegistry, IEditorLanguageRegistry } from "@jupyterlab/codemirror";
import { IRenderMimeRegistry } from "@jupyterlab/rendermime";

/**
 * Main widget constructor options
 */
export interface IDiffWidgetOptions<T> {
  model: T;
  rendermime: IRenderMimeRegistry;
  extensions: IEditorExtensionRegistry;
  languages: IEditorLanguageRegistry;
}
