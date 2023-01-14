

import {
  PathExt, URLExt
} from '@jupyterlab/coreutils';

import type {
  IRenderMimeRegistry
} from '@jupyterlab/rendermime';

import {
  ServerConnection
} from '@jupyterlab/services';

import type {
  Widget
} from '@lumino/widgets';

import {
  NbdimeWidget
} from './widget';

import {
  urlRStrip
} from './utils';



interface IApiResponse {
  is_git: boolean;
}



export
function diffNotebook(args: {
  readonly base: string,
  readonly remote: string,
  readonly rendermime: IRenderMimeRegistry,
  hideUnchanged?: boolean
}): Widget {
  let {base, remote} = args;
  let widget = new NbdimeWidget(args);
  widget.title.label = `Diff: ${base} ↔ ${remote}`;
  widget.title.caption = `Local: ${base}\nRemote: '${remote}'`;
  return widget;
}


export
function diffNotebookCheckpoint(args: {
  readonly path: string,
  readonly rendermime: IRenderMimeRegistry,
  hideUnchanged?: boolean
}): Widget {
  const {path, rendermime, hideUnchanged} = args;
  let nb_dir = PathExt.dirname(path);
  let name = PathExt.basename(path, '.ipynb');
  let base = PathExt.join(nb_dir, name + '.ipynb');
  let widget = new NbdimeWidget({
    base,
    rendermime,
    baseLabel: 'Checkpoint',
    hideUnchanged,
  });
  widget.title.label = `Diff checkpoint: ${name}`;
  widget.title.caption = `Local: latest checkpoint\nRemote: '${path}'`;
  widget.title.iconClass = 'fa fa-clock-o jp-fa-tabIcon';
  return widget;
}


export
function diffNotebookGit(args: {
  readonly path: string,
  readonly rendermime: IRenderMimeRegistry,
  hideUnchanged?: boolean
}): Widget {
  const {path, rendermime, hideUnchanged} = args;
  let name = PathExt.basename(path, '.ipynb');
  let widget = new NbdimeWidget({base: path, rendermime, hideUnchanged});
  widget.title.label = `Diff git: ${name}`;
  widget.title.caption = `Local: git HEAD\nRemote: '${path}'`;
  widget.title.iconClass = 'fa fa-git jp-fa-tabIcon';
  return widget;
}


export
function isNbInGit(args: {readonly path: string}): Promise<boolean> {
  let request = {
      method: 'POST',
      body: JSON.stringify(args),
    };
  let settings = ServerConnection.makeSettings();
  return ServerConnection.makeRequest(
    URLExt.join(urlRStrip(settings.baseUrl), '/nbdime/api/isgit'),
    request, settings).then((response) => {
      if (!response.ok) {
        return Promise.reject(response);
      }
      return response.json() as Promise<IApiResponse>;
    }).then((data) => {
      return data['is_git'];
    });
}
