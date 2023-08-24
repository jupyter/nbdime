const esModules = [
  '@jupyterlab',
  '@codemirror',
  '@jupyter/ydoc',
  'lib0',
  'nanoid',
  'vscode-ws-jsonrpc',
  'y-protocols',
  'y-websocket',
  'yjs'
].join('|');

module.exports = {
  testEnvironment: 'jsdom',
  automock: false,
  moduleNameMapper: {
    '\\.(css|less|sass|scss)$': 'identity-obj-proxy',
    '\\.(svg)$': '<rootDir>/test/jest-file-mock.js',
  },
  transform: {
    // Extracted from https://github.com/kulshekhar/ts-jest/blob/v29.0.3/presets/index.js
    '^.+\\.tsx?$': [
      'ts-jest/legacy',
      {
        tsconfig: `./tsconfig.test.json`
      }
    ],
    '^.+\\.jsx?$': 'babel-jest'
  },
  moduleFileExtensions: ['ts', 'tsx', 'js', 'jsx', 'json', 'node'],
  setupFiles: ['<rootDir>/test/jest-setup-files.js'],
  testPathIgnorePatterns: ['/lib/', '/node_modules/'],
  testRegex: '/test/src/.*.spec.ts$',
  transformIgnorePatterns: [`/node_modules/(?!${esModules}).+`],
  reporters: ['default', 'github-actions'],
};
