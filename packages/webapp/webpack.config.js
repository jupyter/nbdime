const path = require('path');

module.exports = {
	entry: './src/index.ts',
	output: {
		path: path.resolve(__dirname, '..', '..', 'nbdime', 'webapp', 'static'),
		filename: 'nbdime.js',
		publicPath: './static/',
	},
	bail: true,
	devtool: 'source-map',
	module: {
		rules: [
			{
				test: /\.css$/,
				use: [
					require.resolve('style-loader'),
					require.resolve('css-loader'),
				],
			},
			{
				test: /\.ipynb$/,
				type: 'json',
			},
			{
				test: /\.ts$/,
				use: [
					{
						loader: 'swc-loader',
						options: {
							jsc: {
								parser: {
									syntax: 'typescript',
								},
							},
						},
					},
				],
			},
			{
				test: /\.js$/,
				loader: require.resolve('source-map-loader'),
			},
			{ test: /\.html$/, loader: require.resolve('file-loader') }, // jquery-ui loads some images
			{
				test: /\.(jpg|png|gif)$/,
				loader: require.resolve('file-loader'),
			}, // required to load font-awesome
			{
				test: /\.woff2(\?v=\d+\.\d+\.\d+)?$/,
				use: [
					{
						loader: require.resolve('url-loader'),
						options: {
							limit: 10000,
							mimetype: 'application/font-woff',
						},
					},
				],
			},
			{
				test: /\.woff(\?v=\d+\.\d+\.\d+)?$/,
				use: [
					{
						loader: require.resolve('url-loader'),
						options: {
							limit: 10000,
							mimetype: 'application/font-woff',
						},
					},
				],
			},
			{
				test: /\.ttf(\?v=\d+\.\d+\.\d+)?$/,
				use: [
					{
						loader: require.resolve('url-loader'),
						options: {
							limit: 10000,
							mimetype: 'application/octet-stream',
						},
					},
				],
			},
			{
				test: /\.eot(\?v=\d+\.\d+\.\d+)?$/,
				loader: require.resolve('file-loader'),
			},
			{
				test: /\.svg(\?v=\d+\.\d+\.\d+)?$/,
				use: [
					{
						loader: require.resolve('url-loader'),
						options: {
							limit: 10000,
							mimetype: 'image/svg+xml',
						},
					},
				],
			},
		],
	},
	resolve: {
		extensions: ['.webpack.js', '.web.js', '.ts', '.js'],
	},
};
