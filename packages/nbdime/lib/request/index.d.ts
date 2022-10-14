import { JSONObject } from '@lumino/coreutils';
export declare function handleError(response: Response): Promise<Response>;
/**
 * Make a request to an nbdime API.
 */
export declare function requestApiPromise(baseUrl: string, apiPath: string, argument: any): Promise<Response>;
/**
 * Make a request to an nbdime API.
 */
export declare function requestApi(baseUrl: string, apiPath: string, argument: any, onComplete: (result: any) => void, onFail: (errorMessage: string) => void): void;
/**
 * Make a POST request passing a JSON argument and receiving a JSON result.
 */
export declare function requestApiJsonPromise(baseUrl: string, apiPath: string, argument: any): Promise<JSONObject>;
/**
 * Make a POST request passing a JSON argument and receiving a JSON result.
 */
export declare function requestApiJson(baseUrl: string, apiPath: string, argument: any, callback: (result: any) => void, onError: (errorMessage: string) => void): void;
/**
 * Make a diff request for the given base/remote specifiers (filenames)
 */
export declare function requestDiffPromise(base: string, remote: string | undefined, baseUrl: string): Promise<JSONObject>;
/**
 * Make a diff request for the given base/remote specifiers (filenames)
 */
export declare function requestDiff(base: string, remote: string | undefined, baseUrl: string, onComplete: (result: any) => void, onFail: (errorMessage: string) => void): void;
/**
 * Make a diff request for the given base/remote specifiers (filenames)
 */
export declare function requestMergePromise(base: string, local: string, remote: string, baseUrl: string): Promise<JSONObject>;
/**
 * Make a diff request for the given base/remote specifiers (filenames)
 */
export declare function requestMerge(base: string, local: string, remote: string, baseUrl: string, onComplete: (result: any) => void, onFail: (errorMessage: string) => void): void;
//# sourceMappingURL=index.d.ts.map