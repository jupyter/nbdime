// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.

var istanbul = require('istanbul');
var path = require('path');
var collector = new istanbul.Collector();
var reporter = new istanbul.Reporter();

var remappedJson = require('../coverage/remapped.json');
var keys = Object.keys(remappedJson);
var coverage = {};


// Filter out any path that is not local:
var shortPrefix = 'src/';
for (var i = 0; i < keys.length; i++) {
  var key = keys[i].replace(/\\/g, '/');
  if (key.startsWith(shortPrefix)) {
    coverage[ key ] = remappedJson[ keys[i] ];
  } else {
    var longPrefix = path.resolve(__dirname + '/../' + shortPrefix).replace(/\\/g, '/');
    if (key.startsWith(longPrefix)) {
      coverage[ keys[i] ] = remappedJson[ keys[i] ];
    }
  }
}


collector.add(coverage);
reporter.add('html');
reporter.add('lcovonly');
reporter.reports['lcovonly'].file = 'coverage.lcov';
reporter.write(collector, true, function() {});
