import { JSONValue, PartialJSONValue } from '@lumino/coreutils';
import { PanelLayout, Widget } from '@lumino/widgets';
import { IRenderMimeRegistry } from '@jupyterlab/rendermime';
import { RenderableDiffModel } from '../model';
/**
 * Widget for outputs with renderable MIME data.
 */
export declare abstract class RenderableDiffView<T extends (JSONValue | PartialJSONValue)> extends Widget {
    constructor(model: RenderableDiffModel<T>, editorClass: string[], rendermime: IRenderMimeRegistry, mimetype: string);
    layout: PanelLayout;
    mimetype: string;
    /**
     * Create a widget which renders the given cell output
     */
    protected abstract createSubView(data: T, trusted: boolean): Widget;
    protected rendermime: IRenderMimeRegistry;
    protected model: RenderableDiffModel<T>;
}
//# sourceMappingURL=renderable.d.ts.map