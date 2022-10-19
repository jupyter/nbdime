// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.

var fs = require("fs-extra");
fs.copySync("src/", "lib/", {
  filter: (pth) => fs.lstatSync(pth).isDirectory() || /\.css$/.test(pth),
});
fs.copySync("src/", "lib/", {
  filter: (pth) => fs.lstatSync(pth).isDirectory() || /\.svg$/.test(pth),
});
fs.copySync("src/", "lib/", {
  filter: (pth) => fs.lstatSync(pth).isDirectory() || /\.png$/.test(pth),
});
