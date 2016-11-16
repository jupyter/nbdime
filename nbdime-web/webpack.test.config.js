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
      { test: /\.css$/, loader: 'style-loader!css-loader' },
      { test: /\.(json|ipynb)$/, loader: 'json-loader' },
      { test: /\.ts$/, loader: 'ts-loader',
        query: {
          configFileName: './test/src/tsconfig.json'
        }
      },
      { test: /\.html$/, loader: 'file-loader' },
      // jquery-ui loads some images
      { test: /\.(jpg|png|gif)$/, loader: 'file-loader' },
      // required to load font-awesome
      { test: /\.woff2(\?v=\d+\.\d+\.\d+)?$/, loader: 'url-loader?limit=10000&mimetype=application/font-woff' },
      { test: /\.woff(\?v=\d+\.\d+\.\d+)?$/, loader: 'url-loader?limit=10000&mimetype=application/font-woff' },
      { test: /\.ttf(\?v=\d+\.\d+\.\d+)?$/, loader: 'url-loader?limit=10000&mimetype=application/octet-stream' },
      { test: /\.eot(\?v=\d+\.\d+\.\d+)?$/, loader: 'file-loader' },
      { test: /\.svg(\?v=\d+\.\d+\.\d+)?$/, loader: 'url-loader?limit=10000&mimetype=image/svg+xml' }
    ]

  },
  resolve: {
    // Add '.ts' as resolvable extensions.
    extensions: ['', '.webpack.js', '.web.js', '.js', '.ts'],
    modulesDirectories: ['node_modules']
  }
}