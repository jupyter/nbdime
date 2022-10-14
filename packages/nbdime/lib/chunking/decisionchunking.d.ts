import { DiffCollection } from '../diff/diffentries';
import { MergeDecision } from '../merge/decisions';
export declare type MergeChunk = {
    baseStart: number;
    baseEnd: number;
    diffs: DiffCollection;
};
export declare function splitMergeDecisionsOnChunks(base: any[], decisions: MergeDecision[]): MergeDecision[];
//# sourceMappingURL=decisionchunking.d.ts.map