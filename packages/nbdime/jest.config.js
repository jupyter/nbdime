var tsConfig = require ('./tsconfig.json');

var tsOptions = tsConfig["compilerOptions"];
// Need as the test folder is not visible from the src folder
tsOptions["rootDir"] = null;
tsOptions["inlineSourceMap"] = true;
//const jestJupyterLab = require('@jupyterlab/testutils/lib/jest-config');
//const baseConfig = jestJupyterLab(__dirname);

module.exports = {
  //...baseConfig,
  testEnvironment: 'jsdom',
  automock: false,
  moduleNameMapper: {
    '\\.(css|less|sass|scss)$': 'identity-obj-proxy',
    '\\.(svg)$': '<rootDir>/test/jest-file-mock.js'
  },
  preset: 'ts-jest/presets/js-with-babel',
  moduleFileExtensions: ['ts', 'tsx', 'js', 'jsx', 'json', 'node'],
  setupFiles: ['<rootDir>/test/jest-setup-files.js'],
  testPathIgnorePatterns: ['/lib/', '/node_modules/'],
  testRegex: '/test/src/.*.spec.ts$',
  transformIgnorePatterns: ['/node_modules/(?!((@jupyterlab|y-protocols|yjs|@jupyter/ydoc|lib0)/.*))'],
  globals: {
    'ts-jest': {
      tsconfig: tsOptions
    }
  }
};
