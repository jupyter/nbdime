import type { CodeEditor } from '@jupyterlab/codeeditor';

import { PathExt, URLExt } from '@jupyterlab/coreutils';

import type { IRenderMimeRegistry } from '@jupyterlab/rendermime';

import { ServerConnection } from '@jupyterlab/services';

import { nullTranslator, type ITranslator } from '@jupyterlab/translation';

import type { Widget } from '@lumino/widgets';

import { NbdimeWidget } from './widget';

import { urlRStrip } from './utils';

interface IApiResponse {
  is_git: boolean;
}

export function diffNotebook(args: {
  readonly base: string;
  readonly remote: string;
  readonly rendermime: IRenderMimeRegistry;
  readonly editorFactory: CodeEditor.Factory;
  hideUnchanged?: boolean;
  translator?: ITranslator;
}): Widget {
  let { base, remote, translator } = args;
  const trans = (translator ?? nullTranslator).load('nbdime');
  let widget = new NbdimeWidget(args);
  widget.title.label = trans.__('Diff: %1 ↔ %2', base, remote);
  widget.title.caption = trans.__("Local: '%1'\nRemote: '%2'", base, remote);
  return widget;
}

export function diffNotebookCheckpoint(args: {
  readonly path: string;
  readonly rendermime: IRenderMimeRegistry;
  readonly editorFactory: CodeEditor.Factory;
  hideUnchanged?: boolean;
  translator?: ITranslator;
}): Widget {
  const { path, rendermime, hideUnchanged, editorFactory, translator } = args;
  const trans = (translator ?? nullTranslator).load('nbdime');
  let nb_dir = PathExt.dirname(path);
  let name = PathExt.basename(path, '.ipynb');
  let base = PathExt.join(nb_dir, name + '.ipynb');

  let widget = new NbdimeWidget({
    base,
    editorFactory,
    rendermime,
    baseLabel: trans.__('Checkpoint'),
    hideUnchanged,
    translator,
  });
  widget.title.label = trans.__('Diff checkpoint: %1', name);
  widget.title.caption = trans.__(
    "Local: latest checkpoint\nRemote: '%1'",
    path,
  );
  widget.title.iconClass = 'fa fa-clock-o jp-fa-tabIcon';
  return widget;
}

export function diffNotebookGit(args: {
  readonly path: string;
  readonly rendermime: IRenderMimeRegistry;
  readonly editorFactory: CodeEditor.Factory;
  hideUnchanged?: boolean;
  translator?: ITranslator;
}): Widget {
  const { path, rendermime, hideUnchanged, editorFactory, translator } = args;
  const trans = (translator ?? nullTranslator).load('nbdime');
  let name = PathExt.basename(path, '.ipynb');
  let widget = new NbdimeWidget({
    base: path,
    editorFactory,
    rendermime,
    hideUnchanged,
    translator,
  });
  widget.title.label = trans.__('Diff git: %1', name);
  widget.title.caption = trans.__("Local: git HEAD\nRemote: '%1'", path);
  widget.title.iconClass = 'fa fa-git jp-fa-tabIcon';
  return widget;
}

export function isNbInGit(args: { readonly path: string }): Promise<boolean> {
  let request = {
    method: 'POST',
    body: JSON.stringify(args),
  };
  let settings = ServerConnection.makeSettings();
  return ServerConnection.makeRequest(
    URLExt.join(urlRStrip(settings.baseUrl), '/nbdime/api/isgit'),
    request,
    settings,
  )
    .then(response => {
      if (!response.ok) {
        return Promise.reject(response);
      }
      return response.json() as Promise<IApiResponse>;
    })
    .then(data => {
      return data['is_git'];
    });
}
