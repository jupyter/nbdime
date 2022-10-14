import * as nbformat from '@jupyterlab/nbformat';
import { IDiffArrayEntry } from '../diffentries';
import { RenderableDiffModel } from './renderable';
import { IStringDiffModel } from './string';
/**
 * Diff model for single cell output entries.
 *
 * Can converted to a StringDiffModel via the method `stringify()`, which also
 * takes an optional argument `key` which specifies a subpath of the IOutput to
 * make the model from.
 */
export declare class OutputDiffModel extends RenderableDiffModel<nbformat.IOutput> {
    /**
     * Checks whether the given mimetype is present in the output's mimebundle.
     * If so, it returns the path/key to that mimetype's data. If not present,
     * it returns null.
     *
     * See also: innerMimeType
     */
    hasMimeType(mimetype: string): string | string[] | null;
    /**
     * Returns the expected MIME type of the IOutput subpath specified by `key`,
     * as determined by the notebook format specification.
     *
     * Throws an error for unknown keys.
     *
     * See also: hasMimeType
     */
    innerMimeType(key: string | string[]): string;
    /**
     * Can be converted to a StringDiffModel via the method `stringify()`, which also
     * takes an optional argument `key` which specifies a subpath of the IOutput to
     * make the model from.
     */
    stringify(key?: string | string[]): IStringDiffModel;
}
/**
 * Function used to create a list of models for a list diff
 *
 * - If base and remote are both non-null and equal, it returns
 *   a list of models representing unchanged entries.
 * - If base and a diff is given, it ignores remote and returns
 *   a list of models representing the diff.
 * - If base is null, it returns a list of models representing
 *   added entries.
 * - If remote is null, it returns a list of models representing
 *   deleted entries.
 */
export declare function makeOutputModels(base: nbformat.IOutput[] | null, remote: nbformat.IOutput[] | null, diff?: IDiffArrayEntry[] | null): OutputDiffModel[];
//# sourceMappingURL=output.d.ts.map