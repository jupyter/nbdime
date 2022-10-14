import { JSONValue, JSONArray, JSONObject, PartialJSONArray, PartialJSONObject, PartialJSONValue } from '@lumino/coreutils';
import { IDiffEntry } from '../diff/diffentries';
/**
 * Patch a base JSON object according to diff. Returns the patched object.
 */
export declare function patch(base: string, diff: IDiffEntry[] | null): string;
export declare function patch<T extends (PartialJSONArray | JSONArray)>(base: T, diff: IDiffEntry[] | null): T;
export declare function patch<T extends (JSONObject | PartialJSONObject)>(base: T, diff: IDiffEntry[] | null): T;
export declare function patch(base: (JSONValue | PartialJSONValue), diff: IDiffEntry[] | null): JSONValue;
//# sourceMappingURL=generic.d.ts.map