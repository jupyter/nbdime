var path = require('path');

module.exports = {
  context: __dirname,
  entry: './test/src/index.ts',
  output: {
    path: __dirname + "/test/build",
    filename: "test.js",
    devtoolModuleFilenameTemplate: __dirname.replace('\\', '/') + '/[resource-path]'
  },
  bail: true,
  debug: true,
  verbose: true,
  devtool: 'inline-source-map',
  module: {
    loaders: [
      /**
       * Enable inline source maps for code coverage report.
       *
       * See project repository for details / configuration reference:
       * https://github.com/s-panferov/awesome-typescript-loader
       */
      {
          test: /\.ts$/,
          loader: 'awesome-typescript-loader'
      },
      { test: /\.css$/, loader: 'style-loader!css-loader' },
      { test: /\.json$/, loader: 'json-loader' },
      { test: /\.md$/, loader: 'raw-loader'},
      { test: /\.html$/, loader: "file?name=[name].[ext]" },
      { test: /\.ipynb$/, loader: 'json-loader' },
      // jquery-ui loads some images
      { test: /\.(jpg|png|gif)$/, loader: 'file' },
      // required to load font-awesome
      { test: /\.woff2(\?v=\d+\.\d+\.\d+)?$/, loader: 'url?limit=10000&mimetype=application/font-woff' },
      { test: /\.woff(\?v=\d+\.\d+\.\d+)?$/, loader: 'url?limit=10000&mimetype=application/font-woff' },
      { test: /\.ttf(\?v=\d+\.\d+\.\d+)?$/, loader: 'url?limit=10000&mimetype=application/octet-stream' },
      { test: /\.eot(\?v=\d+\.\d+\.\d+)?$/, loader: 'file' },
      { test: /\.svg(\?v=\d+\.\d+\.\d+)?$/, loader: 'url?limit=10000&mimetype=image/svg+xml' }
    ],
    /*preLoaders: [
      // All output '.js' files will have any sourcemaps re-processed by 'source-map-loader'.
      { test: /\.js$/, loader: "source-map-loader" }
    ]
    postLoaders: [
      //Instruments TS source files for subsequent code coverage.
      {
        test: /\.ts$/,
        loader: 'istanbul-instrumenter-loader',
        exclude: [
          'node_modules',
          /\.(spec|d)\.ts$/
        ]
      }
    ]*/
  },
  resolve: {
    // Add '.ts' and '.tsx' as resolvable extensions.
    extensions: ['', '.ts', '.js'],
    modulesDirectories: ['node_modules']
  }
}