// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
'use strict';

import {
  nbformat
} from 'jupyterlab/lib/notebook/notebook/nbformat';

import {
  NotifyUserError
} from '../../common/exceptions';

import {
  IDiffEntry, IDiffArrayEntry
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
 * Diff model for single cell output entries.
 *
 * Can converted to a StringDiffModel via the method `stringify()`, which also
 * takes an optional argument `key` which specifies a subpath of the IOutput to
 * make the model from.
 */
export
class OutputDiffModel implements IDiffModel {
  constructor(
        base: nbformat.IOutput | null,
        remote: nbformat.IOutput | null,
        diff?: IDiffEntry[] | null) {
    if (!remote && !base) {
      throw new Error('Either remote or base value need to be given');
    }
    this.base = base;
    if (!remote && diff) {
      this.remote = patch(base!, diff);
    } else {
      this.remote = remote;
    }
    this.diff = diff || null;
    this.collapsible = false;
  }

  get unchanged() : boolean {
    return this.diff === null && this.base !== null && this.remote !== null;
  }

  get added(): boolean {
    return this.base === null;
  }

  get deleted(): boolean {
    return this.remote === null;
  }

  /**
   * Checks whether the given mimetype is present in the output's mimebundle.
   * If so, it returns the path/key to that mimetype's data. If not present,
   * it returns null.
   *
   * See also: innerMimeType
   */
  hasMimeType(mimetype: string): string | null {
    let outputs = this.base || this.remote!;
    if (outputs.output_type === 'stream' &&
          mimetype === 'application/vnd.jupyter.console-text') {
      return 'text';
    } else if (outputs.output_type === 'execute_result' || outputs.output_type === 'display_data') {
      let data = outputs.data;
      if (mimetype in data) {
        return 'data.' + mimetype;
      }
    }
    return null;
  }

  /**
   * Returns the expected MIME type of the IOutput subpath specified by `key`,
   * as determined by the notebook format specification.
   *
   * Throws an error for unknown keys.
   *
   * See also: hasMimeType
   */
  innerMimeType(key: string) : string {
    let t = (this.base || this.remote!).output_type;
    if (t === 'stream' && key === 'text') {
      // TODO: 'application/vnd.jupyter.console-text'?
      return 'text/plain';
    } else if ((t === 'execute_result' || t === 'display_data') &&
          key.indexOf('data.') === 0) {
      return key.slice('data.'.length);
    }
    throw new NotifyUserError('Unknown MIME type for key: ' + key);
  }

  /**
   * Can converted to a StringDiffModel via the method `stringify()`, which also
   * takes an optional argument `key` which specifies a subpath of the IOutput to
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
    model.mimetype = key ? this.innerMimeType(key) : 'application/json';
    model.collapsible = this.collapsible;
    model.collapsibleHeader = this.collapsibleHeader;
    model.startCollapsed = this.startCollapsed;
    return model;
  }

  /**
   * Base value
   */
  base: nbformat.IOutput | null;

  /**
   * Remote value
   */
  remote: nbformat.IOutput | null;

  /**
   * Diff entries between base and remote
   */
  diff: IDiffEntry[] | null;

  // ICollapsibleModel:
  collapsible: boolean;
  collapsibleHeader: string;
  startCollapsed: boolean;
}




export
function makeOutputModels(base: nbformat.IOutput[] | null,
                          remote: nbformat.IOutput[] | null,
                          diff?: IDiffArrayEntry[] | null) : OutputDiffModel[] {
  let models: OutputDiffModel[] = [];
  if (remote === null && !diff) {
    if (base === null) {
      throw new Error('Either base or remote need to be specififed!');
    }
    // Cell deleted
    for (let o of base) {
      models.push(new OutputDiffModel(o, null));
    }
  } else if (base === null) {
    if (remote === null) {
      throw new Error('Either base or remote need to be specififed!');
    }
    // Cell added
    for (let o of remote) {
      models.push(new OutputDiffModel(null, o));
    }
  } else if (remote === base) {
    // Outputs unchanged
    for (let o of base) {
      models.push(new OutputDiffModel(o, o));
    }
  } else if (diff) {
    // Outputs' patched, remote will be null
    let consumed = 0;
    let skip = 0;
    for (let d of diff) {
      let index = d.key;
      for (let o of base.slice(consumed, index)) {
        // Add unchanged outputs
        models.push(new OutputDiffModel(o, o));
      }
      if (d.op === 'addrange') {
        // Outputs added
        for (let o of d.valuelist) {
          models.push(new OutputDiffModel(null, o));
        }
        skip = 0;
      } else if (d.op === 'removerange') {
        // Outputs removed
        let len = d.length;
        for (let i = index; i < index + len; i++) {
          models.push(new OutputDiffModel(base[i], null));
        }
        skip = len;
      } else if (d.op === 'patch') {
        // Output changed
        models.push(new OutputDiffModel(
          base[index], null, d.diff));
        skip = 1;
      } else {
        throw new Error('Invalid diff operation: ' + d);
      }
      consumed = Math.max(consumed, index + skip);
    }
    for (let o of base.slice(consumed)) {
      // Add unchanged outputs
      models.push(new OutputDiffModel(o, o));
    }
  } else {
    throw new Error('Invalid arguments to OutputsDiffModel');
  }
  return models;
}
