import { CodeEditor } from '@jupyterlab/codeeditor';
import { IRenderMimeRegistry } from '@jupyterlab/rendermime';

/**
 * Main widget constructor options
 */
// TODO `T` should be scoped down but more API rework will be needed on the model to achieve that
// there is definitely room to rationalize the code with more abstract or mixin classes.
export interface IDiffWidgetOptions<T> {
  model: T;
  rendermime: IRenderMimeRegistry;
  editorFactory?: CodeEditor.Factory;
}

export interface ICellDiffWidgetOptions<T> extends IDiffWidgetOptions<T> {
  // TODO this seems redundant as mimetype is part of the model
  mimetype: string;
}
