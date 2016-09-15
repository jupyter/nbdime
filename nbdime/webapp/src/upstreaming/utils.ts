// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.

/**
 * Apply a mixin
 */
export
function applyMixins(derivedCtor: any, baseCtors: any[]) {
    baseCtors.forEach(baseCtor => {
        Object.getOwnPropertyNames(baseCtor.prototype).forEach(name => {
            let desc = Object.getOwnPropertyDescriptor(baseCtor.prototype, name);
            Object.defineProperty(derivedCtor.prototype, name, desc);
        });
    });
}
