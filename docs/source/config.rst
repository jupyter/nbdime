Configuration
=============

Nbdime uses a config system loosely based on that of Jupyter. This means that
it looks for config files ``nbdime_config.json`` in all the directories listed
by the ``jupyter --paths`` command. The syntax of the config files are similar
to that of other Jupyter commands::

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



Sections
--------

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



Configuring ignores
-------------------

The config system allows for detailed control over what to ignore or not
via the "Ignore" key. It takes a dictionary in the following format::


    "Ignore": {
      "/cells/*/outputs": True,
      "/cells/*/attachments": False,
      "/cells/*/metadata": ["collapsed", "autoscroll", "deletable", "editable"]
    }

Which will ignore outputs, specify that attachments should not be ignored, and
ignore the cell metadata keys as specified in the list. In general, the list
syntax for keys are used for ignoring leaf-nodes, that is, things that are not
a sequence or map (`[]` or `{}`).


Configurations of "Ignore" in different sections will be merged, such that
non-conflicting keys will all be added. If the keys (diff paths) overlap,
the most specific section's value will be taken. As an example, take the following
config::

    {
      "Diff": {
        "Ignore": {
          "/metadata": ["foo"],
          "/cells/*/metadata": ["tags"]
        }
      },
      "GitDiff": {
        "Ignore": {
          "/cells/*/outputs": True,
          "/cells/*/metadata": ["collapsed", "autoscroll", "deletable", "editable"]
        }
      }
    }

Here, the final config for a git diff entry point will be::

    {
      "Ignore": {
        "/metadata": ["foo"],
        "/cells/*/outputs": True,
        "/cells/*/metadata": ["collapsed", "autoscroll", "deletable", "editable"]
      }
    }

This means that the "tags" entry from the "Diff" section is not automatically
included in the merge.
