module.exports = {
	sourceMap: 'inline',
	presets: [
		[
			'@babel/preset-env',
			{
				targets: {
					node: '14',
				},
			},
		],
	],
};
