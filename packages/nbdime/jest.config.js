module.exports = {
	automock: false,
	moduleNameMapper: {
		'\\.(css|less|sass|scss)$': 'identity-obj-proxy',
		'\\.(svg)$': '<rootDir>/test/jest-file-mock.js',
	},
	transform: {
		'^.+\\.(t|j)sx?$': [
			'@swc/jest',
			{
				jsc: {
					target: 'es2020',
				},
			},
		],
	},
	moduleFileExtensions: ['ts', 'tsx', 'js', 'jsx', 'json', 'node'],
	extensionsToTreatAsEsm: ['.ts', '.tsx'],
	setupFiles: ['<rootDir>/test/jest-setup-files.js'],
	testPathIgnorePatterns: ['/lib/', '/node_modules/'],
	testRegex: '/test/src/.*.spec.ts$',
	transformIgnorePatterns: ['<rootDir>/node_modules/'],
};
