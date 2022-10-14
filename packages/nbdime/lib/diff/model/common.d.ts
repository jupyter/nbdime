/**
 * Describes a model whose view can be collapsible.
 *
 * Intended as hints for a view of the model, and not a requirement.
 */
export interface ICollapsibleModel {
    /**
     * Whether a view of the model should be collapsible (hint)
     */
    collapsible: boolean;
    /**
     * String to show in header of collapser element
     */
    collapsibleHeader: string;
    /**
     * The initial state of a collapsible view
     */
    startCollapsed: boolean;
}
/**
 * Base interface for diff models.
 */
export interface IDiffModel extends ICollapsibleModel {
    /**
     * Is diff no-op?
     */
    unchanged: boolean;
    /**
     * Whether diff represents a simple addition
     */
    added: boolean;
    /**
     * Whether diff represents a simple deletion
     */
    deleted: boolean;
}
//# sourceMappingURL=common.d.ts.map