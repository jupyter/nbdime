module.exports = function (config) {
  config.set({
    basePath: '..',
    frameworks: ['mocha', 'karma-typescript'],
    files: [
      { pattern: "test/src/**/*.ts" },
      { pattern: "src/**/*.ts" }
    ],
    exclude: [
      "src/request/**/*.*"
    ],
    port: 9876,
    colors: true,
    singleRun: true,
    logLevel: config.LOG_INFO,

    preprocessors: {
      '**/*.ts': ['karma-typescript']
    },

    reporters: ['mocha', 'karma-typescript'],

    karmaTypescriptConfig: {
      tsconfig: 'test/src/tsconfig.json'
    }
  });
};