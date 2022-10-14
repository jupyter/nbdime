import { JSONValue, PartialJSONValue } from '@lumino/coreutils';
import { Signal } from '@lumino/signaling';
import { IDiffEntry } from '../diffentries';
import { IDiffModel } from './common';
import { IStringDiffModel } from './string';
/**
 * Diff model for a renderable object (something that has an internal MimeBundle)
 *
 * Can be converted to a StringDiffModel via the method `stringify()`, which also
 * takes an optional argument `key` which specifies a subpath of the IOutput to
 * make the model from.
 */
export declare abstract class RenderableDiffModel<T extends (JSONValue | PartialJSONValue)> implements IDiffModel {
    constructor(base: T | null, remote: T | null, diff?: IDiffEntry[] | null);
    get unchanged(): boolean;
    get added(): boolean;
    get deleted(): boolean;
    /**
     * Checks whether the given mimetype is present in the entry's mimebundle.
     * If so, it returns the path/key to that mimetype's data. If not present,
     * it returns null.
     */
    abstract hasMimeType(mimetype: string): string | string[] | null;
    /**
     * Get the mimetype for a given key from hasMimeType.
     */
    abstract innerMimeType(key: string | string[]): string;
    /**
     * Convert to a StringDiffModel.
     *
     * Takes an optional argument `key` which specifies a subpath of the MimeBundle to
     * make the model from.
     */
    stringify(key?: string | string[]): IStringDiffModel;
    /**
     * Base value
     */
    base: T | null;
    /**
     * Remote value
     */
    remote: T | null;
    /**
     * Diff entries between base and remote
     */
    diff: IDiffEntry[] | null;
    /**
     * Whether outputs are trusted
     */
    get trusted(): boolean;
    set trusted(value: boolean);
    /**
     * The present values of model.base/remote
     */
    get contents(): T[];
    trustedChanged: Signal<RenderableDiffModel<T>, boolean>;
    collapsible: boolean;
    collapsibleHeader: string;
    startCollapsed: boolean;
    private _trusted;
}
//# sourceMappingURL=renderable.d.ts.map