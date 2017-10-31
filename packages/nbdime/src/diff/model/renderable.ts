// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
'use strict';

import {
  JSONValue
} from '@phosphor/coreutils';

import {
  IDiffEntry
} from '../diffentries';

import {
  getSubDiffByKey
} from '../util';

import {
  patch
} from '../../patch';

import {
  IDiffModel
} from './common';

import {
  IStringDiffModel, createDirectStringDiffModel, createPatchStringDiffModel
} from './string';



/**
 * Diff model for a renderable object (something that has an internal MimeBundle)
 *
 * Can be converted to a StringDiffModel via the method `stringify()`, which also
 * takes an optional argument `key` which specifies a subpath of the IOutput to
 * make the model from.
 */
export
abstract class RenderableDiffModel<T extends JSONValue> implements IDiffModel {
  constructor(
        base: T | null,
        remote: T | null,
        diff?: IDiffEntry[] | null) {
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

  get unchanged() : boolean {
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
  abstract hasMimeType(mimetype: string): string | null;

  /**
   * Convert to a StringDiffModel.
   *
   * Takes an optional argument `key` which specifies a subpath of the MimeBundle to
   * make the model from.
   */
  stringify(key?: string) : IStringDiffModel {
    let getMemberByPath = function(obj: any, key: string, f?: (obj: any, key: string) => any): any {
      if (!obj) {
        return obj;
      }
      let i = key.indexOf('.');
      if (i >= 0) {
        console.assert(i < key.length);
        if (f) {
          return getMemberByPath(
            f(obj, key.slice(0, i)), key.slice(i + 1), f);
        }
        return getMemberByPath(
          obj[key.slice(0, i)], key.slice(i + 1), f);
      } else if (f) {
        return f(obj, key);
      }
      return obj[key];
    };
    let base = key ? getMemberByPath(this.base, key) as any : this.base;
    let remote = key ? getMemberByPath(this.remote, key) as any : this.remote;
    let diff = (this.diff && key) ?
      getMemberByPath(this.diff, key, getSubDiffByKey) as IDiffEntry[] | null :
      this.diff;
    let model: IStringDiffModel | null = null;
    if (this.unchanged || this.added || this.deleted || !diff) {
      model = createDirectStringDiffModel(base, remote);
    } else {
      model = createPatchStringDiffModel(base, diff);
    }
    model.mimetype = key || 'application/json';
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

  // ICollapsibleModel:
  collapsible: boolean;
  collapsibleHeader: string;
  startCollapsed: boolean;
}
