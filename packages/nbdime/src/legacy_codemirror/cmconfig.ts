
export namespace LegacyCodeMirror {
    export interface EditorConfiguration {
        /** string| The starting value of the editor. Can be a string, or a document object. */
        value?: any;

        /** Whether CodeMirror should scroll or wrap for long lines. Defaults to false (scroll). */
        lineWrap?: boolean;

        /** Whether to show line numbers to the left of the editor. */
        lineNumbers?: boolean;

        /** This disables editing of the editor content by the user. If the special value "nocursor" is given (instead of simply true), focusing of the editor is also disallowed. */
        readOnly?: boolean;
    }
}
