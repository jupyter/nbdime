// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.

import type {
  JupyterFrontEndPlugin,
  JupyterFrontEnd,
} from '@jupyterlab/application';

import { CommandToolbarButton } from '@jupyterlab/apputils';

import { IEditorServices } from '@jupyterlab/codeeditor';

import { PathExt } from '@jupyterlab/coreutils';

import type { DocumentRegistry } from '@jupyterlab/docregistry';

import { IRenderMimeRegistry } from '@jupyterlab/rendermime';

import type { INotebookModel } from '@jupyterlab/notebook';

import { NotebookPanel, INotebookTracker } from '@jupyterlab/notebook';

import { ISettingRegistry } from '@jupyterlab/settingregistry';

import { ITranslator, nullTranslator } from '@jupyterlab/translation';

import { find } from '@lumino/algorithm';

import type { CommandRegistry } from '@lumino/commands';

import { IDisposable, DisposableDelegate } from '@lumino/disposable';

import { diffNotebookGit, diffNotebookCheckpoint, isNbInGit } from './actions';

const pluginId = 'nbdime-jupyterlab:plugin';

const INITIAL_NETWORK_RETRY = 2; // ms

export class NBDiffExtension
  implements DocumentRegistry.IWidgetExtension<NotebookPanel, INotebookModel>
{
  /**
   *
   */
  constructor(commands: CommandRegistry) {
    this.commands = commands;
  }

  /**
   * Create a new extension object.
   */
  createNew(
    nb: NotebookPanel,
    context: DocumentRegistry.IContext<INotebookModel>,
  ): IDisposable {
    // Create extension here

    // Add buttons to toolbar
    let buttons: CommandToolbarButton[] = [];
    let insertionPoint = -1;
    find(nb.toolbar.children(), (tbb, index) => {
      if (tbb.hasClass('jp-Notebook-toolbarCellType')) {
        insertionPoint = index;
        return true;
      }
      return false;
    });
    let i = 1;
    for (let id of [
      CommandIDs.diffNotebookCheckpoint,
      CommandIDs.diffNotebookGit,
    ]) {
      let button = new CommandToolbarButton({
        commands: this.commands,
        id,
      });
      button.addClass('nbdime-toolbarButton');
      if (insertionPoint >= 0) {
        nb.toolbar.insertItem(
          insertionPoint + i++,
          this.commands.label(id),
          button,
        );
      } else {
        nb.toolbar.addItem(this.commands.label(id), button);
      }
      buttons.push(button);
    }

    return new DisposableDelegate(() => {
      // Cleanup extension here
      for (let btn of buttons) {
        btn.dispose();
      }
    });
  }

  protected commands: CommandRegistry;
}

export namespace CommandIDs {
  export const diffNotebook = 'nbdime:diff';

  export const diffNotebookGit = 'nbdime:diff-git';

  export const diffNotebookCheckpoint = 'nbdime:diff-checkpoint';
}

function addCommands(
  app: JupyterFrontEnd,
  tracker: INotebookTracker,
  rendermime: IRenderMimeRegistry,
  settings: ISettingRegistry.ISettings,
  editorServices: IEditorServices,
  translator: ITranslator,
): void {
  const { commands, shell } = app;
  const editorFactory = editorServices.factoryService.newInlineEditor.bind(
    editorServices.factoryService,
  );
  const trans = translator.load('nbdime');

  /**
   * Error message if the nbdime API is unavailable.
   */
  const serverMissingMsg = trans.__(
    'Unable to query nbdime API. Is the server extension enabled?',
  );

  // Whether we have our server extension available
  let hasAPI = true;

  /**
   * Whether there is an active notebook.
   */
  function baseEnabled(): boolean {
    return hasAPI && tracker.currentWidget !== null;
  }

  // This allows quicker checking, but if someone creates/removes
  // a repo during the session, this will become incorrect
  let lut_known_git: { [key: string]: boolean } = {};

  let networkRetry = INITIAL_NETWORK_RETRY;

  /**
   * Whether the notebook is in a git repository.
   */
  function hasGitNotebook(): boolean {
    if (!baseEnabled()) {
      return false;
    }

    let path = tracker.currentWidget!.context.path;
    let dir = PathExt.dirname(path);
    let known_git = lut_known_git[dir];
    if (known_git === undefined) {
      const inGitPromise = isNbInGit({ path: dir });
      inGitPromise.then(inGit => {
        networkRetry = INITIAL_NETWORK_RETRY;
        lut_known_git[dir] = inGit;
        // Only update if false, since it is left enabled while waiting
        if (!inGit) {
          commands.notifyCommandChanged(CommandIDs.diffNotebookGit);
        }
      });
      inGitPromise.catch(reason => {
        hasAPI = reason.status !== undefined && reason.status !== 404;
        setTimeout(() => {
          networkRetry *= 2;
          commands.notifyCommandChanged(CommandIDs.diffNotebook);
          commands.notifyCommandChanged(CommandIDs.diffNotebookCheckpoint);
          commands.notifyCommandChanged(CommandIDs.diffNotebookGit);
        }, networkRetry);
      });
      // Leave button enabled while unsure
      return true;
    }

    return known_git;
  }

  function erroredGen(text: string) {
    return () => {
      if (hasAPI) {
        return text;
      }
      return serverMissingMsg;
    };
  }

  let hideUnchanged = settings.get('hideUnchanged').composite !== false;
  settings.changed.connect(() => {
    hideUnchanged = settings.get('hideUnchanged').composite !== false;
  });

  commands.addCommand(CommandIDs.diffNotebook, {
    execute: args => {
      // TODO: Check args for base/remote
      // if missing, prompt with dialog.
      //let content = current.notebook;
      //diffNotebook({base, remote, translator});
    },
    label: erroredGen(trans.__('Notebook diff')),
    caption: erroredGen(trans.__('Display nbdiff between two notebooks')),
    isEnabled: baseEnabled,
    iconClass:
      'jp-Icon jp-Icon-16 action-notebook-diff action-notebook-diff-notebooks',
    iconLabel: 'nbdiff',
  });

  commands.addCommand(CommandIDs.diffNotebookCheckpoint, {
    execute: args => {
      let current = tracker.currentWidget;
      if (!current) {
        return;
      }
      let widget = diffNotebookCheckpoint({
        path: current.context.path,
        editorFactory,
        rendermime,
        hideUnchanged,
        translator,
      });
      shell.add(widget);
      if (args['activate'] !== false) {
        shell.activateById(widget.id);
      }
    },
    label: erroredGen(trans.__('Notebook checkpoint diff')),
    caption: erroredGen(
      trans.__('Display nbdiff from checkpoint to currently saved version'),
    ),
    isEnabled: baseEnabled,
    iconClass:
      'jp-Icon jp-Icon-16 fa fa-clock-o action-notebook-diff action-notebook-diff-checkpoint',
  });

  commands.addCommand(CommandIDs.diffNotebookGit, {
    execute: args => {
      let current = tracker.currentWidget;
      if (!current) {
        return;
      }
      let widget = diffNotebookGit({
        path: current.context.path,
        editorFactory,
        rendermime,
        hideUnchanged,
        translator,
      });
      shell.add(widget);
      if (args['activate'] !== false) {
        shell.activateById(widget.id);
      }
    },
    label: erroredGen(trans.__('Notebook Git diff')),
    caption: erroredGen(
      trans.__('Display nbdiff from git HEAD to currently saved version'),
    ),
    isEnabled: hasGitNotebook,
    iconClass:
      'jp-Icon jp-Icon-16 fa fa-git action-notebook-diff action-notebook-diff-git',
  });
}

/**
 * The notebook diff provider.
 */
const nbDiffProvider: JupyterFrontEndPlugin<void> = {
  id: pluginId,
  requires: [
    INotebookTracker,
    IRenderMimeRegistry,
    ISettingRegistry,
    IEditorServices,
  ],
  optional: [ITranslator],
  activate: activateWidgetExtension,
  autoStart: true,
};

export default nbDiffProvider;

/**
 * Activate the widget extension.
 */
async function activateWidgetExtension(
  app: JupyterFrontEnd,
  tracker: INotebookTracker,
  rendermime: IRenderMimeRegistry,
  settingsRegistry: ISettingRegistry,
  editorServices: IEditorServices,
  translator: ITranslator | null,
): Promise<void> {
  let { commands, docRegistry } = app;
  let extension = new NBDiffExtension(commands);
  docRegistry.addWidgetExtension('Notebook', extension);

  const settings = await settingsRegistry.load(pluginId);
  addCommands(
    app,
    tracker,
    rendermime,
    settings,
    editorServices,
    translator ?? nullTranslator,
  );
  // Update the command registry when the notebook state changes.
  tracker.currentChanged.connect(() => {
    commands.notifyCommandChanged(CommandIDs.diffNotebookGit);
    if (tracker.size <= 1) {
      commands.notifyCommandChanged(CommandIDs.diffNotebook);
      commands.notifyCommandChanged(CommandIDs.diffNotebookCheckpoint);
    }
  });
}
