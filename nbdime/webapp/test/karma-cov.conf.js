var shared = require('./karma.conf.js');
module.exports = function(config) {
  shared(config);
  config.set({
    reporters: ['mocha', 'coverage', 'remap-coverage'],

    preprocessors: {
      'test/build/bundle.js': ['sourcemap', 'coverage']
    },

    coverageReporter: {
      type: 'in-memory'
    },

    remapCoverageReporter: {
      'text-summary': null,
      lcovonly: 'coverage.lcov'
     }
  });
};
