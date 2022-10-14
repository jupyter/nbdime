import * as nbformat from '@jupyterlab/nbformat';
import { IDiffEntry } from '../../diff/diffentries';
import { IStringDiffModel } from '../../diff/model';
import { MergeDecision } from '../../merge/decisions';
import { ObjectMergeModel } from './common';
/**
 * Model of a merge of metadata with decisions
 */
export declare class MetadataMergeModel extends ObjectMergeModel<nbformat.INotebookMetadata, IStringDiffModel> {
    constructor(base: nbformat.INotebookMetadata, decisions: MergeDecision[]);
    serialize(): nbformat.INotebookMetadata;
    protected createDiffModel(diff: IDiffEntry[]): IStringDiffModel;
    protected createMergedDiffModel(): IStringDiffModel;
    base: nbformat.INotebookMetadata;
}
//# sourceMappingURL=metadata.d.ts.map