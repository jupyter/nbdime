import type { CodeEditor } from '@jupyterlab/codeeditor';
import type { IRenderMimeRegistry } from '@jupyterlab/rendermime';

/**
 * Common merge view options
 */
export interface IMergeWidgetOptions {
  /**
   * Whether to show the base version (4-panels) or not (3-panels).
   */
  showBase?: boolean;
}

/**
 * Main widget constructor options
 */
// TODO `T` should be scoped down but more API rework will be needed on the model to achieve that
// there is definitely room to rationalize the code with more abstract or mixin classes.
export interface IDiffWidgetOptions<T> {
  model: T;
  editorFactory?: CodeEditor.Factory;
}

export interface IMimeDiffWidgetOptions<T> {
  model: T;
  rendermime: IRenderMimeRegistry;
  editorFactory?: CodeEditor.Factory;
}

export interface ICellDiffWidgetOptions<T> extends IMimeDiffWidgetOptions<T> {
  // TODO this seems redundant as mimetype is part of the model
  mimetype: string;
}
