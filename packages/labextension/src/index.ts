// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.

import NBDiffProvider from './plugin';

import 'nbdime/lib/common/collapsible.css';
import 'nbdime/lib/upstreaming/flexpanel.css';
import 'nbdime/lib/common/dragpanel.css';
import 'nbdime/lib/styles/variables.css';
import 'nbdime/lib/styles/common.css';
import 'nbdime/lib/styles/diff.css';
import 'nbdime/lib/styles/merge.css';

import '../style/index.css'

export default NBDiffProvider;

export {
  INBDiffExtension
} from './plugin';
