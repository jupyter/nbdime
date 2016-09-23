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
     },

     customLaunchers: {
        Chrome_travis_ci: {
            base: 'Chrome',
            flags: ['--no-sandbox']
        }
    },
  });

  if (process.env.TRAVIS && !config.browsers) {
    config.browsers = ['Chrome_travis_ci'];
  }
};
