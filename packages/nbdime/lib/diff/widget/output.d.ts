import * as nbformat from '@jupyterlab/nbformat';
import { Panel, Widget } from '@lumino/widgets';
import { IRenderMimeRegistry } from '@jupyterlab/rendermime';
import { RenderableDiffView } from './renderable';
import { CellDiffModel, OutputDiffModel } from '../model';
/**
 * A panel responsible for rendering an output diff
 */
export declare class OutputPanel extends Panel {
    /**
     *
     */
    constructor(model: OutputDiffModel, parentModel: CellDiffModel, editorClasses: string[], rendermime: IRenderMimeRegistry);
    /**
     * Add view to panel, possibly wrapped
     */
    protected initContainer(view: Widget): void;
    /**
     * Replace a view with a new one
     */
    protected replaceView(view: Widget): void;
    /**
     * Create a text or rendered view of the output diff model
     */
    protected createView(forceText?: boolean): Widget;
    /**
     * Create text view of output
     */
    protected createOutputTextView(): Widget;
    /**
     * Creates a menu that is shown when hovering over the output.
     *
     * Stored in this.menu.
     */
    protected createHoverMenu(): void;
    /**
     * Update trusted status
     */
    protected trustedChanged(trusted: boolean): void;
    /**
     * Update view
     */
    protected updateView(): void;
    protected get selectedMimetype(): string | null;
    protected set selectedMimetype(value: string | null);
    protected model: OutputDiffModel;
    protected rendermime: IRenderMimeRegistry;
    protected editorClasses: string[];
    protected container: Panel;
    protected view: Widget;
    protected menu: Panel;
    protected _mimetype: string | null;
    protected forceText: boolean;
    /**
     * Whether trust can affect the output rendering.
     */
    static isTrustSignificant(model: OutputDiffModel, rendermime: IRenderMimeRegistry): boolean;
}
/**
 * Widget for an output with renderable MIME data.
 */
export declare class RenderableOutputView extends RenderableDiffView<nbformat.IOutput> {
    constructor(model: OutputDiffModel, editorClass: string[], rendermime: IRenderMimeRegistry, mimetype: string);
    /**
     * Create a widget which renders the given cell output
     */
    protected createSubView(output: nbformat.IOutput, trusted: boolean): Widget;
    /**
     * Update trusted status
     */
    updateView(mimeType: string, trusted: boolean): void;
    protected model: OutputDiffModel;
    /**
     * Checks if a cell output can be rendered (either safe/trusted or
     * sanitizable)
     */
    static canRender(model: OutputDiffModel, rendermime: IRenderMimeRegistry): boolean;
}
//# sourceMappingURL=output.d.ts.map