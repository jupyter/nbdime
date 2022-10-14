// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
'use strict';
Object.defineProperty(exports, "__esModule", { value: true });
exports.NotifyUserError = void 0;
/**
 * An error that should be displayed to the user
 */
class NotifyUserError extends Error {
    constructor(message, severity = 'error') {
        super(message);
        // Set the prototype explicitly.
        Object.setPrototypeOf(this, NotifyUserError.prototype);
        this.message = message;
        this.stack = new Error().stack;
        this.severity = severity;
    }
}
exports.NotifyUserError = NotifyUserError;
//# sourceMappingURL=exceptions.js.map