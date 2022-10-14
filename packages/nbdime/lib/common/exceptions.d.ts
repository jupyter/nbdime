/**
 * An error that should be displayed to the user
 */
export declare class NotifyUserError extends Error {
    constructor(message: string, severity?: NotifyUserError.Severity);
    severity: NotifyUserError.Severity;
}
export declare namespace NotifyUserError {
    /**
     * Severity of an error.
     *
     * Anything less severe that warning shouldn't
     * use an exception.
     */
    type Severity = 'error' | 'warning';
}
//# sourceMappingURL=exceptions.d.ts.map