module.exports = function (config) {
  config.set({
    basePath: '..',
    frameworks: ['mocha'],
    files: [
      'test/build/test.js'
      ],
    port: 9876,
    colors: true,
    singleRun: true,
    logLevel: config.LOG_INFO,

    preprocessors: {
      'test/build/test.js': ['sourcemap', 'coverage'],
    },
    reporters: ['mocha', 'coverage', 'remap-coverage'],

    // save interim raw coverage report in memory
    coverageReporter: {
      type: 'in-memory'
    },

    remapCoverageReporter: {
      // Text summary is currently before remapping to TS,
      // so disabled.
      //'text-summary': null, // to show summary in console
      json: './coverage/remapped.json'
    },
  });
};