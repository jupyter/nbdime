import * as CodeMirror from 'codemirror';
import { ChunkSource } from '../chunking';
/**
 * Represents a range in a diff (typically in a string), in absolute indices (1D)
 */
export declare class DiffRangeRaw {
    /**
     * Create a new range [from, to = from + length)
     */
    constructor(from: number, length: number, source?: ChunkSource);
    /**
     * Change both `from` and `to` fields by the given offset
     */
    offset(offset: number): void;
    /**
     * The starting index of the range.
     */
    from: number;
    /**
     * The final index of the range (non-inclusive, compatible with .slice())
     */
    to: number;
    /**
     * Diff source for merging
     */
    source?: ChunkSource;
}
/**
 * Class representing a string (diff) range in the format of
 * CodeMirror.Positions. Mainly makes sense for string diffs.
 *
 * The class also has fields to ease chunking of diffs without reparsing the
 * text.
 */
export declare class DiffRangePos {
    from: CodeMirror.Position;
    to: CodeMirror.Position;
    /**
     * Create a diff range. The `ch` field of the `to` position is defined as
     * non-inclusive, i.e., it follows the syntax of String.slice().
     */
    constructor(from: CodeMirror.Position, to: CodeMirror.Position, chunkStartLine?: boolean, endsOnNewline?: boolean);
    /**
     * Whether to include the first line of the range (from.line) when chunking.
     * If false, from.line + 1 should be used instead.
     *
     * Typically used when the diff starts with a newline.
     */
    chunkStartLine: boolean;
    /**
     * Whether the diff represented by the range ends on a newline.
     */
    endsOnNewline: boolean;
    /**
     * Diff source for merging
     */
    source?: ChunkSource;
}
/**
 * Function to convert an array of DiffRangeRaw to DiffRangePos. The
 * `text` parameter is the text in which the ranges exist.
 */
export declare function raw2Pos(raws: DiffRangeRaw[], text: string): DiffRangePos[];
//# sourceMappingURL=range.d.ts.map