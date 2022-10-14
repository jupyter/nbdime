// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
'use strict';
Object.defineProperty(exports, "__esModule", { value: true });
exports.createCheckbox = exports.MERGE_CLASSES = exports.TWOWAY_DELETION_CLASS = exports.TWOWAY_ADDITION_CLASS = exports.ONEWAY_REMOTE_CLASS = exports.ONEWAY_LOCAL_CLASS = exports.UNCHANGED_MERGE_CLASS = void 0;
const widgets_1 = require("@lumino/widgets");
// Merge classes:
exports.UNCHANGED_MERGE_CLASS = 'jp-Merge-unchanged';
exports.ONEWAY_LOCAL_CLASS = 'jp-Merge-oneway-local';
exports.ONEWAY_REMOTE_CLASS = 'jp-Merge-oneway-remote';
exports.TWOWAY_ADDITION_CLASS = 'jp-Merge-twoway-addition';
exports.TWOWAY_DELETION_CLASS = 'jp-Merge-twoway-deletion';
const BASE_MERGE_CLASS = 'jp-Merge-base';
const LOCAL_MERGE_CLASS = 'jp-Merge-local';
const REMOTE_MERGE_CLASS = 'jp-Merge-remote';
const MERGED_MERGE_CLASS = 'jp-Merge-merged';
exports.MERGE_CLASSES = [BASE_MERGE_CLASS, LOCAL_MERGE_CLASS,
    REMOTE_MERGE_CLASS, MERGED_MERGE_CLASS];
/**
 * Create a widget containing a checkbox with a label.
 *
 * @export
 * @param {boolean} value - The initial check state (true = checked)
 * @param {string} text - The text of the label
 * @returns {{checkbox: HTMLInputElement, widget: Widget }}
 */
function createCheckbox(value, text, indeterminate = false) {
    let checkbox = document.createElement('input');
    checkbox.setAttribute('type', 'checkbox');
    checkbox.checked = value;
    checkbox.indeterminate = indeterminate;
    // Create label for checkbox:
    let widget = new widgets_1.Widget();
    let label = document.createElement('label');
    label.innerHTML = text;
    // Combine checkbox and label:
    label.insertBefore(checkbox, label.childNodes[0]);
    // Add checkbox to header:
    widget.node.appendChild(label);
    return { checkbox, widget };
}
exports.createCheckbox = createCheckbox;
//# sourceMappingURL=common.js.map