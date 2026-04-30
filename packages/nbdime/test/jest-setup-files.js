global.fetch = require('jest-fetch-mock');

const noop = () => {};

const defineWindowProperty = (name, value) => {
  Object.defineProperty(window, name, {
    configurable: true,
    writable: true,
    value,
  });
};

const createMediaQueryList = query => ({
  matches: false,
  media: query,
  onchange: null,
  addListener: noop,
  removeListener: noop,
  addEventListener: noop,
  removeEventListener: noop,
  dispatchEvent: () => false,
});

class NoopObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
}

// jsdom does not implement these browser APIs, but JupyterLab UI dependencies
// expect them to exist.
defineWindowProperty('DragEvent', class DragEvent {});
defineWindowProperty('matchMedia', createMediaQueryList);
defineWindowProperty('ResizeObserver', NoopObserver);
defineWindowProperty('IntersectionObserver', NoopObserver);
