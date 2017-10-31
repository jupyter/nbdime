// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
'use strict';

import {
  Widget
} from '@phosphor/widgets';


// Merge classes:
export const UNCHANGED_MERGE_CLASS = 'jp-Merge-unchanged';
export const ONEWAY_LOCAL_CLASS = 'jp-Merge-oneway-local';
export const ONEWAY_REMOTE_CLASS = 'jp-Merge-oneway-remote';
export const TWOWAY_ADDITION_CLASS = 'jp-Merge-twoway-addition';
export const TWOWAY_DELETION_CLASS = 'jp-Merge-twoway-deletion';

const BASE_MERGE_CLASS = 'jp-Merge-base';
const LOCAL_MERGE_CLASS = 'jp-Merge-local';
const REMOTE_MERGE_CLASS = 'jp-Merge-remote';
const MERGED_MERGE_CLASS = 'jp-Merge-merged';

export const MERGE_CLASSES = [BASE_MERGE_CLASS, LOCAL_MERGE_CLASS,
  REMOTE_MERGE_CLASS, MERGED_MERGE_CLASS];


/**
 * Create a widget containing a checkbox with a label.
 *
 * @export
 * @param {boolean} value - The initial check state (true = checked)
 * @param {string} text - The text of the label
 * @returns {{checkbox: HTMLInputElement, widget: Widget }}
 */
export
function createCheckbox(value: boolean, text: string, indeterminate=false): {checkbox: HTMLInputElement, widget: Widget } {
  let checkbox = document.createElement('input');
  checkbox.setAttribute('type', 'checkbox');
  checkbox.checked = value;
  checkbox.indeterminate = indeterminate;
  // Create label for checkbox:
  let widget = new Widget();
  let label = document.createElement('label');
  label.innerHTML = text;
  // Combine checkbox and label:
  label.insertBefore(checkbox, label.childNodes[0]);
  // Add checkbox to header:
  widget.node.appendChild(label);
  return {checkbox, widget};
}
