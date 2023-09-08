// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
'use strict';

import {
  JSONValue,
  JSONObject,
  JSONExt,
  JSONArray,
  PartialJSONValue,
} from '@lumino/coreutils';

import { Signal } from '@lumino/signaling';

import type { IDiffEntry } from '../diffentries';

import { getSubDiffByKey } from '../util';

import { patch } from '../../patch';

import type { IDiffModel } from './common';

import {
  IStringDiffModel,
  createDirectStringDiffModel,
  createPatchStringDiffModel,
} from './string';

/**
 * Diff model for a renderable object (something that has an internal MimeBundle)
 *
 * Can be converted to a StringDiffModel via the method `stringify()`, which also
 * takes an optional argument `key` which specifies a subpath of the IOutput to
 * make the model from.
 */
export abstract class RenderableDiffModel<
  T extends JSONValue | PartialJSONValue,
> implements IDiffModel
{
  constructor(base: T | null, remote: T | null, diff?: IDiffEntry[] | null) {
    if (!remote && !base) {
      throw new Error('Either remote or base value need to be given');
    }
    this.base = base;
    if (!remote && diff) {
      this.remote = patch(base!, diff) as T;
    } else {
      this.remote = remote;
    }
    this.diff = diff || null;
    this.collapsible = false;
  }

  get unchanged(): boolean {
    return JSON.stringify(this.base) === JSON.stringify(this.remote);
  }

  get added(): boolean {
    return this.base === null;
  }

  get deleted(): boolean {
    return this.remote === null;
  }

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
  stringify(key?: string | string[]): IStringDiffModel {
    let getMemberByPath = function (
      obj: JSONValue | null,
      key: string | string[],
      f?: (obj: any, key: string) => any,
    ): JSONValue | null {
      if (!obj) {
        return obj;
      }
      if (Array.isArray(key)) {
        const tail = key.length > 2 ? key.slice(1) : key[1];
        if (f) {
          return getMemberByPath(f(obj, key[0]), tail, f);
        }
        return getMemberByPath((obj as JSONObject)[key[0]], tail, f);
      } else if (f) {
        return f(obj, key);
      }
      return (obj as JSONObject)[key];
    };
    const baseCopy = JSONExt.deepCopy(this.base) as JSONObject;
    let base = key ? getMemberByPath(baseCopy, key) : baseCopy;
    const remoteCopy = JSONExt.deepCopy(this.remote) as JSONObject;
    let remote = key ? getMemberByPath(remoteCopy, key) : remoteCopy;
    let diff =
      this.diff && key
        ? (getMemberByPath(this.diff as any, key, getSubDiffByKey) as
            | IDiffEntry[]
            | null)
        : this.diff;
    let model: IStringDiffModel | null = null;
    if (this.unchanged || this.added || this.deleted || !diff) {
      model = createDirectStringDiffModel(base, remote);
    } else {
      model = createPatchStringDiffModel(
        base as string | JSONObject | JSONArray,
        diff,
      );
    }
    model.mimetype = key ? this.innerMimeType(key) : 'application/json';
    model.collapsible = this.collapsible;
    model.collapsibleHeader = this.collapsibleHeader;
    model.startCollapsed = this.startCollapsed;
    return model;
  }

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
  get trusted(): boolean {
    return this._trusted;
  }
  set trusted(value: boolean) {
    if (this._trusted !== value) {
      this._trusted = value;
      this.trustedChanged.emit(value);
    }
  }

  /**
   * The present values of model.base/remote
   */
  get contents(): T[] {
    let ret: T[] = [];
    if (this.base) {
      ret.push(this.base);
    }
    if (this.remote && this.remote !== this.base) {
      ret.push(this.remote);
    }
    return ret;
  }

  trustedChanged = new Signal<RenderableDiffModel<T>, boolean>(this);

  // ICollapsibleModel:
  collapsible: boolean;
  collapsibleHeader: string;
  startCollapsed: boolean;

  private _trusted: boolean;
}
