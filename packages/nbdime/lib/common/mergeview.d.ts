import * as CodeMirror from 'codemirror';
import { Panel } from '@lumino/widgets';
import { IStringDiffModel } from '../diff/model';
import { DiffRangePos } from '../diff/range';
import { Chunk } from '../chunking';
import { EditorWidget } from './editor';
export declare type Marker = CodeMirror.LineHandle | CodeMirror.TextMarker;
export declare enum DIFF_OP {
    DIFF_DELETE = -1,
    DIFF_INSERT = 1,
    DIFF_EQUAL = 0
}
export declare enum EventDirection {
    INCOMING = 0,
    OUTGOING = 1
}
export declare type DiffClasses = {
    [key: string]: string;
    chunk: string;
    start: string;
    end: string;
    insert: string;
    del: string;
    connect: string;
    gutter: string;
};
/**
 * A wrapper view for showing StringDiffModels in a MergeView
 */
export declare function createNbdimeMergeView(remote: IStringDiffModel): MergeView;
export declare function createNbdimeMergeView(remote: IStringDiffModel | null, local: IStringDiffModel | null, merged: IStringDiffModel, readOnly?: boolean): MergeView;
/**
 * Used by MergeView to show diff in a string diff model
 */
export declare class DiffView {
    constructor(model: IStringDiffModel, type: 'left' | 'right' | 'merge', updateCallback: (force?: boolean) => void, options: CodeMirror.MergeView.MergeViewEditorConfiguration);
    init(base: CodeMirror.Editor): void;
    setShowDifferences(val: boolean): void;
    syncModel(): void;
    buildGap(): HTMLElement;
    setScrollLock(val: boolean, action?: boolean): void;
    protected registerUpdate(): (mode?: "full" | undefined) => void;
    protected modelInvalid(): boolean;
    protected onGutterClick(instance: CodeMirror.Editor, line: number, gutter: string, clickEvent: MouseEvent): void;
    protected registerScroll(): void;
    /**
     * Sync scrolling between base and own editors. `type` is used to indicate
     * which editor is the source, and which editor is the destination of the sync.
     */
    protected syncScroll(type: EventDirection): void;
    protected updateMarks(editor: CodeMirror.Editor, diff: DiffRangePos[], markers: Marker[], type: DIFF_OP): void;
    get ownEditor(): CodeMirror.Editor;
    ownWidget: EditorWidget;
    model: IStringDiffModel;
    type: string;
    showDifferences: boolean;
    dealigned: boolean;
    forceUpdate: Function;
    baseEditor: CodeMirror.Editor;
    chunks: Chunk[];
    lineChunks: Chunk[];
    gap: HTMLElement;
    lockScroll: boolean;
    updating: boolean;
    updatingFast: boolean;
    collapsedRanges: {
        line: number;
        size: number;
    }[];
    protected updateCallback: (force?: boolean) => void;
    protected copyButtons: HTMLElement;
    protected lockButton: HTMLElement;
    protected classes: DiffClasses | null;
}
export interface IMergeViewEditorConfiguration extends CodeMirror.EditorConfiguration {
    /**
     * When true stretches of unchanged text will be collapsed. When a number is given, this indicates the amount
     * of lines to leave visible around such stretches (which defaults to 2). Defaults to false.
     */
    collapseIdentical?: boolean | number;
    /**
     * Original value, not used
     */
    orig: any;
    /**
     * Provides remote diff of document to be shown on the right of the base.
     * To create a diff view, provide only remote.
     */
    remote: IStringDiffModel | null;
    /**
     * Provides local diff of the document to be shown on the left of the base.
     * To create a diff view, omit local.
     */
    local?: IStringDiffModel | null;
    /**
     * Provides the partial merge input for a three-way merge.
     */
    merged?: IStringDiffModel;
    /**
     * When true, the base of a three-way merge is shown. Defaults to true.
     */
    showBase?: boolean;
    /**
     * When true, changed pieces of text are highlighted. Defaults to true.
     */
    showDifferences?: boolean;
}
export declare class MergeView extends Panel {
    constructor(options: IMergeViewEditorConfiguration);
    alignViews(force?: boolean): void;
    setShowDifferences(val: boolean): void;
    getMergedValue(): string;
    left: DiffView | null;
    right: DiffView | null;
    merge: DiffView | null;
    base: EditorWidget;
    options: any;
    diffViews: DiffView[];
    aligners: CodeMirror.LineWidget[];
    initialized: boolean;
    collapsedRanges: {
        size: number;
        line: number;
    }[];
}
//# sourceMappingURL=mergeview.d.ts.map