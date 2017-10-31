// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.

var fs = require('fs-extra');
fs.copySync('src/', 'lib/', { filter: pth => /\.css$/.test(pth) });
fs.copySync('src/', 'lib/', { filter: pth => /\.svg$/.test(pth) });
fs.copySync('src/', 'lib/', { filter: pth => /\.png$/.test(pth) });
