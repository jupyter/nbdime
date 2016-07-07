module.exports = {
  entry: './build/index.js',
  output: {
    path: __dirname + "/static",
    filename: "bundle.js",
    publicPath: "./build/"
  },
  debug: true,
  devtool: 'source-map',
  module: {
    loaders: [
      { test: /\.css$/, loader: 'style-loader!css-loader' },
      { test: /\.json$/, loader: 'json-loader' },
      { test: /\.html$/, loader: 'file' },
    ]
  }
}