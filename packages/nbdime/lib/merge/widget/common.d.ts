import { Widget } from '@lumino/widgets';
export declare const UNCHANGED_MERGE_CLASS = "jp-Merge-unchanged";
export declare const ONEWAY_LOCAL_CLASS = "jp-Merge-oneway-local";
export declare const ONEWAY_REMOTE_CLASS = "jp-Merge-oneway-remote";
export declare const TWOWAY_ADDITION_CLASS = "jp-Merge-twoway-addition";
export declare const TWOWAY_DELETION_CLASS = "jp-Merge-twoway-deletion";
export declare const MERGE_CLASSES: string[];
/**
 * Create a widget containing a checkbox with a label.
 *
 * @export
 * @param {boolean} value - The initial check state (true = checked)
 * @param {string} text - The text of the label
 * @returns {{checkbox: HTMLInputElement, widget: Widget }}
 */
export declare function createCheckbox(value: boolean, text: string, indeterminate?: boolean): {
    checkbox: HTMLInputElement;
    widget: Widget;
};
//# sourceMappingURL=common.d.ts.map