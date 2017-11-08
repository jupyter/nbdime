// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
'use strict';

import {
  nbformat
} from '@jupyterlab/coreutils';

import {
  NotifyUserError
} from '../../common/exceptions';

import {
  IDiffArrayEntry
} from '../diffentries';

import {
  RenderableDiffModel
} from './renderable';

import {
  IStringDiffModel
} from './string';


const TEXT_MIMETYPES = ['text/plain', 'application/vnd.jupyter.stdout',
                        'application/vnd.jupyter.stderr'];


/**
 * Diff model for single cell output entries.
 *
 * Can converted to a StringDiffModel via the method `stringify()`, which also
 * takes an optional argument `key` which specifies a subpath of the IOutput to
 * make the model from.
 */
export
class OutputDiffModel extends RenderableDiffModel<nbformat.IOutput> {

  /**
   * Checks whether the given mimetype is present in the output's mimebundle.
   * If so, it returns the path/key to that mimetype's data. If not present,
   * it returns null.
   *
   * See also: innerMimeType
   */
  hasMimeType(mimetype: string): string | null {
    let outputs = this.base || this.remote!;
    if (nbformat.isStream(outputs) &&
        TEXT_MIMETYPES.indexOf(mimetype) !== -1) {
      return 'text';
    } else if (nbformat.isError(outputs)) {
      return 'traceback';
    } else if (nbformat.isExecuteResult(outputs) || nbformat.isDisplayData(outputs)) {
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
  protected innerMimeType(key: string) : string {
    let t = (this.base || this.remote!).output_type;
    if (t === 'stream' && key === 'text' || t === 'error' && key === 'traceback') {
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
    let model = super.stringify(key);
    if (key) {
       model.mimetype = this.innerMimeType(key);
    }
    return model;
  }
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
    // All entries unchanged
    for (let o of base) {
      models.push(new OutputDiffModel(o, o));
    }
  } else if (diff) {
    // Entries patched, remote will be null
    let consumed = 0;
    let skip = 0;
    for (let d of diff) {
      let index = d.key;
      for (let o of base.slice(consumed, index)) {
        // Add unchanged entries
        models.push(new OutputDiffModel(o, o));
      }
      if (d.op === 'addrange') {
        // Entries added
        for (let o of d.valuelist) {
          models.push(new OutputDiffModel(null, o));
        }
        skip = 0;
      } else if (d.op === 'removerange') {
        // Entries removed
        let len = d.length;
        for (let i = index; i < index + len; i++) {
          models.push(new OutputDiffModel(base[i], null));
        }
        skip = len;
      } else if (d.op === 'patch') {
        // Entry changed
        models.push(new OutputDiffModel(
          base[index], null, d.diff));
        skip = 1;
      } else {
        throw new Error('Invalid diff operation: ' + d);
      }
      consumed = Math.max(consumed, index + skip);
    }
    for (let o of base.slice(consumed)) {
      // Add unchanged entries
      models.push(new OutputDiffModel(o, o));
    }
  } else {
    throw new Error('Invalid arguments to makeOutputModels()');
  }
  return models;
}
