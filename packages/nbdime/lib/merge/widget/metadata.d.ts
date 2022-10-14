import * as nbformat from '@jupyterlab/nbformat';
import { Panel } from '@lumino/widgets';
import { MergeView } from '../../common/mergeview';
import { MetadataMergeModel } from '../model';
/**
 * MetadataWidget for changes to Notebook-level metadata
 */
export declare class MetadataMergeWidget extends Panel {
    constructor(model: MetadataMergeModel);
    init(): void;
    validateMerged(candidate: nbformat.INotebookMetadata): nbformat.INotebookMetadata;
    protected view: MergeView;
    private _model;
}
//# sourceMappingURL=metadata.d.ts.map