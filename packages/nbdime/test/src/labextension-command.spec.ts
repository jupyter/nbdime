// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.

jest.mock('../../../labextension/src/actions', () => ({
  diffNotebook: jest.fn(() => ({ id: 'notebook-diff' })),
  diffNotebookCheckpoint: jest.fn(),
  diffNotebookGit: jest.fn(),
  isNbInGit: jest.fn(() => Promise.resolve(true)),
}));

import { CommandRegistry } from '@lumino/commands';

import { diffNotebook } from '../../../labextension/src/actions';
import nbdimePlugin, { CommandIDs } from '../../../labextension/src/plugin';

describe('nbdime:diff command', () => {
  it('opens a notebook diff for the supplied paths', async () => {
    const commands = new CommandRegistry();
    const add = jest.fn();
    const activateById = jest.fn();
    const app = {
      commands,
      shell: { add, activateById },
      docRegistry: { addWidgetExtension: jest.fn() },
      serviceManager: { serverSettings: {} },
    };
    const tracker = {
      currentWidget: { context: { path: 'current.ipynb' } },
      currentChanged: { connect: jest.fn() },
      size: 1,
    };
    const settings = {
      changed: { connect: jest.fn() },
      get: jest.fn(() => ({ composite: true })),
    };
    const settingsRegistry = {
      load: jest.fn(() => Promise.resolve(settings)),
    };
    const editorFactory = jest.fn();
    const editorServices = {
      factoryService: { newInlineEditor: editorFactory },
    };

    await (nbdimePlugin.activate as any)(
      app,
      tracker,
      {},
      settingsRegistry,
      editorServices,
      null,
    );

    expect(await commands.describedBy(CommandIDs.diffNotebook)).toMatchObject({
      args: {
        type: 'object',
        properties: {
          base: { type: 'string', description: expect.any(String) },
          remote: { type: 'string', description: expect.any(String) },
          activate: { type: 'boolean', description: expect.any(String) },
        },
      },
    });

    await commands.execute(CommandIDs.diffNotebook, {
      base: ' base.ipynb ',
      remote: ' remote.ipynb ',
    });

    expect(diffNotebook).toHaveBeenCalledWith(
      expect.objectContaining({
        base: 'base.ipynb',
        remote: 'remote.ipynb',
      }),
    );
    expect(add).toHaveBeenCalledWith({ id: 'notebook-diff' });
    expect(activateById).toHaveBeenCalledWith('notebook-diff');
  });
});
