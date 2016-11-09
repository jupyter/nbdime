// Type definitions for alertify 0.3.11
// Project: http://fabien-d.github.io/alertify.js/
// Definitions by: John Jeffery <http://github.com/jjeffery>
// Definitions: https://github.com/DefinitelyTyped/DefinitelyTyped

declare var alertify: alertify.IAlertify;

declare namespace alertify {
    interface IAlertify {
        /**
         * Create an alert dialog box
         * @param message   The message passed from the callee
         * @param onOkay    Callback function
         * @param onCancel  Callback function
         * @return alertify (ie this)
         * @since 0.0.1
         */
        alert(message: string, onOkay?: Function, onCancel?: Function): IAlertify;

        /**
         * Set the cancel button label
         * @param label     The label to use
         * @return alertify (ie this)
         * @since 0.0.1
         */
        cancelBtn(label: string): IAlertify;

        /**
         * Clear any log notifications
         * @return alertify (ie this)
         * @since 0.0.1
         */
        clearLogs(): IAlertify;

        /**
         * Set whether logs should close on click
         * @param bool      The value
         * @return alertify (ie this)
         * @since 0.0.1
         */
        closeLogOnClick(bool: boolean): IAlertify;

        /**
         * Create a confirm dialog box
         * @param message   The message passed from the callee
         * @param onOkay    Callback function when OK is clicked
         * @param onCancel  Callback function when cancel is clicked
         * @return alertify (ie this)
         * @since 0.0.1
         */
        confirm(message: string, onOkay?: Function, onCancel?: Function): IAlertify;

        /**
         * Set the default value for dialog input prompt
         * @param str       The new default value
         * @return alertify (ie this)
         * @since 0.0.1
         */
        defaultValue(str: string): IAlertify;

        /**
         * Set the delay. Defaults to 5000 (5s).
         * @param time      Time (in ms) to wait before automatically hiding the message. If 0, never hide.
         * @return alertify (ie this)
         * @since 0.0.1
         */
        delay(time: number | string): IAlertify;

        /**
         * Shorthand for log messages
         * @param message   The message passed from the callee
         * @param click     Click event listener
         * @return alertify (ie this)
         * @since 0.0.1
         */
        error(message: string, click?: (this: this, ev: MouseEvent) => any): IAlertify;

        /**
         * Show a new log message box
         * @param message   The message passed from the callee
         * @param click     Click event listener
         * @return alertify (ie this)
         * @since 0.0.1
         */
        log(message: string, click?: (this: this, ev: MouseEvent) => any): IAlertify;

        /**
         * Set the position of log notification. Defaults to "bottom left".
         * @param str       A string of one or more of "left", "right", "top", "bottom", separated by whitespace.
         * @return alertify (ie this)
         * @since 0.0.1
         */
        logPosition(str: string): IAlertify;

        /**
         * Set the maximum number of log/success/error messages that will be displayed at a single time. The default is 2.
         * @param num       The maximum number of message to display.
         * @return alertify (ie this)
         * @since 0.0.1
         */
        maxLogItems(num: number): IAlertify;

        /**
         * Set the OK button label
         * @param label     The label to use
         * @return alertify (ie this)
         * @since 0.0.1
         */
        okBtn(label: string): IAlertify;

        /**
         * Set the parent element where Alertify is appended into the DOM. By default, Alertify is appended to document.body.
         * @param elem     The parent element.
         * @since 0.0.1
         */
        parent(elem: HTMLElement): void;

        /**
         * Set the placeholder value for the prompt input
         * @param str       The placeholder string
         * @return alertify (ie this)
         * @since 0.0.1
         */
        placeholder(str: string): IAlertify;

        /**
         * Create a prompt dialog box
         * @param message   The message passed from the callee
         * @param onOkay    Callback function when OK is clicked
         * @param onCancel  Callback function when cancel is clicked
         * @return alertify (ie this)
         * @since 0.0.1
         */
        prompt(message: string, onOkay?: Function, onCancel?: Function): IAlertify;

        /**
         * Reset alertify settings
         * @return alertify (ie this)
         * @since 0.0.1
         */
        reset(): IAlertify;

        /**
         * Shorthand for log messages
         * @param message   The message passed from the callee
         * @param click     Click event listener
         * @return alertify (ie this)
         * @since 0.0.1
         */
        success(message: string, click?: (this: this, ev: MouseEvent) => any): IAlertify;

        /**
         * Set the log template method
         * @param templateMethod Template method
         * @return alertify      (ie this)
         * @since 0.0.1
         */
        setLogTemplate(templateMethod: ((message: string) => string) | null): IAlertify;

        /**
         * Set the theme to use for dialogs
         * @return alertify      (ie this)
         * @since 0.0.1
         */
        theme(themeStr: 'bootstrap' | 'purecss' | 'mdl' | 'material-design-light' | 'angular-material' | 'default'): IAlertify;

        /**
         * The version of alertify
         * @since 0.0.1
         */
        version: string;
    }
}

declare module "alertify.js" {

    export = alertify;

}
