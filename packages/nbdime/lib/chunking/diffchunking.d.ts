import { IDiffEntry } from '../diff/diffentries';
import { DiffRangePos } from '../diff/range';
import { MergeDecision } from '../merge/decisions';
export declare type ChunkSource = {
    decision: MergeDecision;
    action: 'local' | 'remote' | 'either' | 'custom';
};
/**
 * A chunk is a range of lines in a string based diff
 * that logically belong together.
 *
 * Chunks can be used for:
 *  - Correlating diff entries in the base and remote, e.g.
 *    for aligning lines in two editors.
 *  - Finding parts of the unchanged text that are not needed
 *    as context (can be hidden)
 *  - Navigating a diff ("Go to next diff")
 */
export declare class Chunk {
    baseFrom: number;
    baseTo: number;
    remoteFrom: number;
    remoteTo: number;
    constructor(baseFrom: number, baseTo: number, remoteFrom: number, remoteTo: number, source?: ChunkSource);
    /**
     * Indicates the source of a chunk in a merge condition.
     *
     * For merged content this can be used to indicate whther the chunk originates
     * from base, local, remote or somewhere else.
     */
    sources: ChunkSource[];
    /**
     * Checks whether the given line number is within the range spanned by editFrom - editTo
     */
    inEdit(line: number): boolean;
    /**
     * Checks whether the given line number is within the range spanned by origFrom - origTo
     */
    inOrig(line: number): boolean;
}
export declare class Chunker {
    constructor();
    protected _getCurrent(): Chunk | null;
    protected _overlapChunk(chunk: Chunk, range: DiffRangePos, isAddition: boolean): boolean;
    addDiff(range: DiffRangePos, isAddition: boolean): void;
    /**
     * Chunk a region where changes will occur if a currently unapplied diff were
     * applied.
     */
    addGhost(range: DiffRangePos, isAddition: boolean, offset: number): void;
    chunks: Chunk[];
    editOffset: number;
    protected _currentGhost: Chunk | null;
}
/**
 * A chunker that only chunks diffs within lines with each other
 *
 * While the default chunker would chunk together a change at the end of one
 * line with a change at the start of the next line, this chunker will keep
 * each line separate. This is useful e.g. for merging.
 */
export declare class LineChunker extends Chunker {
    protected _overlapChunk(chunk: Chunk, range: DiffRangePos, isAddition: boolean): boolean;
}
/**
 * Transform an array of lines to normal chunks
 */
export declare function lineToNormalChunks(lineChunks: Chunk[]): Chunk[];
/**
 * Label a set of diffs with a source, recursively.
 */
export declare function labelSource(diff: IDiffEntry[] | null, source: ChunkSource): IDiffEntry[] | null;
//# sourceMappingURL=diffchunking.d.ts.map