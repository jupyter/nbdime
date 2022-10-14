import { Panel } from '@lumino/widgets';
import { IStringDiffModel } from '../model';
/**
 * MetadataWidget for changes to Notebook-level metadata
 */
export declare class MetadataDiffWidget extends Panel {
    constructor(model: IStringDiffModel);
    init(): void;
    private _model;
}
//# sourceMappingURL=metadata.d.ts.map