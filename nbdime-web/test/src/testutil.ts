// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.

import {
  nbformat
} from '@jupyterlab/services';


export
const notebookStub: nbformat.INotebookContent = {
  'cells': [
  ],
  'metadata': {
    'kernelspec': {
      'display_name': 'Python 2',
      'language': 'python',
      'name': 'python2'
    },
    'language_info': {
      'codemirror_mode': {
      'name': 'ipython',
      'version': 2
      },
      'file_extension': '.py',
      'mimetype': 'text/x-python',
      'name': 'python',
      'nbconvert_exporter': 'python',
      'pygments_lexer': 'ipython2',
      'version': '2.7.11'
    },
    'orig_nbformat': 4
  },
  'nbformat': 4,
  'nbformat_minor': 0
}

export
const codeCellStub: nbformat.ICodeCell = {
  cell_type: 'code',
  execution_count: 0,
  metadata: {
    trusted: true
  },
  source: [''],
  outputs: []
}

