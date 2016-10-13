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
      'test/build/test.js': ['sourcemap'],
    },
    reporters: ['mocha']
  });
};