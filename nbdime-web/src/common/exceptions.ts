// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.

'use strict';


/**
 * An error that should be displayed to the user
 */
export
class NotifyUserError extends Error {
  constructor(
      message: string,
      severity: NotifyUserError.Severity = 'error') {
    super(message);
    this.message = message;
    this.stack = new Error().stack;
    this.severity = severity;
  }

  severity: NotifyUserError.Severity;
}

export
namespace NotifyUserError {
  /**
   * Severity of an error.
   *
   * Anything less severe that warning shouldn't
   * use an exception.
   */
  export
  type Severity = 'error' | 'warning';

}

