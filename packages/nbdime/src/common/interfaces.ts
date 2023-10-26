import type { CodeEditor } from '@jupyterlab/codeeditor';
import type { IRenderMimeRegistry } from '@jupyterlab/rendermime';
import type { ITranslator } from '@jupyterlab/translation';

/**
 * Diff view options
 */
export interface IDiffViewOptions {
  /**
   * When true stretches of unchanged text will be collapsed in the text editors.
   * When a number is given, this indicates the amount of lines to leave visible
   * around such stretches (which defaults to 2). Defaults to true.
   */
  collapseIdentical?: boolean | number;
  /**
   * The translation manager.
   */
  translator?: ITranslator;
}

/**
 * Common merge view options
 */
export interface IMergeViewOptions extends IDiffViewOptions {
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
export interface IDiffWidgetOptions<T> extends IDiffViewOptions {
  /**
   * Diff model
   */
  model: T;
  /**
   * Text editor factory
   */
  editorFactory?: CodeEditor.Factory;
}

export interface IMimeDiffWidgetOptions<T> extends IDiffWidgetOptions<T> {
  /**
   * Rendermime registry
   */
  rendermime: IRenderMimeRegistry;
}

export interface ICellDiffWidgetOptions<T> extends IMimeDiffWidgetOptions<T> {
  /**
   * Cell mime type
   */
  // TODO this seems redundant as mimetype is part of the model
  mimetype: string;
}
