// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
'use strict';

/**
 * Check whether a value is in an array.
 */
export function valueIn(value: any, array: Array<any>) {
  return array.indexOf(value) >= 0;
}
