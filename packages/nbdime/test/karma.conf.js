const base = require('./karma-nocov.conf');

module.exports = function (config) {
  base(config)
  config.set({
    karmaTypescriptConfig: {
      coverageOptions: {
        instrumentation: true
      },
      reports: {
        "text-summary": "",
        "html": "coverage",
        "lcovonly": {
          "directory": "coverage",
          "filename": "coverage.lcov"
        }
      }
    }
  });
};