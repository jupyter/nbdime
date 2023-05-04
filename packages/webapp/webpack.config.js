const path = require('path');

module.exports = {
  entry: './src/index.ts',
  output: {
    path: path.resolve(__dirname, '..', '..', 'nbdime', 'webapp', 'static'),
    filename: 'nbdime.js',
    publicPath: './static/'
  },
  bail: true,
  devtool: 'source-map',
  module: {
    rules: [
      { test: /\.css$/, use: ['style-loader', 'css-loader'] },
      { test: /\.ipynb$/, type: 'json' },
      { test: /\.ts$/, loader: 'ts-loader' },
      { test: /\.js$/, loader: 'source-map-loader' },
      { test: /\.html$/, loader: 'file-loader' },
      // jquery-ui loads some images
      { test: /\.(jpg|png|gif)$/, type: 'asset/resource' },
      // required to load font-awesome
      { test: /\.woff2(\?v=\d+\.\d+\.\d+)?$/, type: 'asset' },
      { test: /\.woff(\?v=\d+\.\d+\.\d+)?$/, type: 'asset' },
      { test: /\.ttf(\?v=\d+\.\d+\.\d+)?$/, type: 'asset' },
      { test: /\.eot(\?v=\d+\.\d+\.\d+)?$/, type: 'asset/resource' },
      { test: /\.svg(\?v=\d+\.\d+\.\d+)?$/, type: 'asset' }
    ]
  },
  resolve: {
    // Add '.ts' as resolvable extension.
    extensions: ['.webpack.js', '.web.js', '.ts', '.js']
  }
};
