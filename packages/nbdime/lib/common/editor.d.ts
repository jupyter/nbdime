import { Widget } from '@lumino/widgets';
import { CodeEditorWrapper } from '@jupyterlab/codeeditor';
import { CodeMirrorEditor } from '@jupyterlab/codemirror';
export declare class EditorWidget extends CodeEditorWrapper {
    /**
     * Store all editor instances for operations that
     * need to loop over all instances.
     */
    constructor(value?: string, options?: Partial<CodeMirrorEditor.IConfig>);
    static editors: CodeMirror.Editor[];
    get cm(): CodeMirror.Editor;
    get doc(): CodeMirror.Doc;
    /**
     * A message handler invoked on an `'resize'` message.
     */
    protected onResize(msg: Widget.ResizeMessage): void;
    staticLoaded: boolean;
}
//# sourceMappingURL=editor.d.ts.map