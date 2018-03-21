Configuration
=============

Nbdime uses a config system loosely based on that of Jupyter. This means that
it looks for config files ``nbdime_config.json`` or ``nbdime_config.py`` in all
the directories listed by the ``jupyter --paths`` command. The syntax of the
config files are similar to that of other Jupyter commands. For Python config::

    # Sample config file
    c.NbDiff.details = False

For JSON config::

    {
      "NbDiff": {
        "details": false
      }
    }

To list all the possible config options and their *current effective values*
run the command::

    nbdime --config

Alternatively, you can use the ``--config`` flag for any CLI entry point::

    nbdiff --config
    nbmerge --config

Any flags passed on the CLI will override the config value.

To make it easier to configure the options of several commands at the same
time, you can use the following config sections:


Global
    Options to apply to all commands.

Web
    Options to web commands (Server, NbDiffWeb, NbMergeWeb, NbDiffTool,
    NbMergeTool).

WebTool
    Options to web tool commands (NbDiffTool, NbMergeTool).

Diff
    Options to diffing commands (NbDiff, NbDiffWeb, NbDiffDriver,
    NbDiffTool).

Merge
    Options to merge commands (NbMerge, NbMergeWeb, NbMergeDriver,
    NbMergeTool).

GitDiff
    Options to git diff commands (NbDiffDriver, NbDiffTool)

GitMerge
    Options to git diff commands (NbMergeDriver, NbMergeTool)
