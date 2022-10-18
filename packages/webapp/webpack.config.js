const path = require('path');

module.exports = {
	entry: './src/index.ts',
	output: {
		path: path.join(__dirname, '../../nbdime/webapp/static'),
		filename: 'nbdime.js',
		publicPath: './static/',
	},
	bail: true,
	devtool: 'eval-cheap-module-source-map',
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
				test: /\.(html|jpg|png|gif|svg)$/,
				type: 'asset/resource',
			},
			{
				test: /\.((?:woff2?|ttf|eot)(?:\?v=.*)?|)$/,
				type: 'asset/resource',
			},
		],
	},
	infrastructureLogging: {
		level: 'error',
	},
	resolve: {
		extensions: ['.ts', '.js', '.json'],
	},
};
