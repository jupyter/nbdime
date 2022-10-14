import { Widget, Panel } from '@lumino/widgets';
/**
 * CollapsiblePanel
 */
export declare class CollapsiblePanel extends Panel {
    static createHeader(headerTitle?: string): Panel;
    constructor(inner: Widget, headerTitle?: string, collapsed?: boolean);
    toggleCollapsed(): void;
    get collapsed(): boolean;
    set headerTitle(value: string);
    inner: Widget;
    header: Panel;
    slider: Panel;
    container: Panel;
    button: HTMLElement;
}
//# sourceMappingURL=collapsiblepanel.d.ts.map