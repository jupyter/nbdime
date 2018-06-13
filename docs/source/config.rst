Configuration
=============

Nbdime uses a config system loosely based on that of Jupyter. This means that
it looks for config files ``nbdime_config.json`` in all the directories listed
by the ``jupyter --paths`` command, as well as the current working directory.
The syntax of the config files are similar to that of other Jupyter commands::

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

The current output of `nbdime --config` is:

.. code-block:: none

    All available config options, and their current values:

    NbDiff:
      Ignore: {}
      attachments: null
      color_words: false
      details: null
      metadata: null
      outputs: null
      source: null

    NbDiffWeb:
      Ignore: {}
      attachments: null
      base_url: "/"
      browser: null
      color_words: false
      details: null
      ip: "127.0.0.1"
      metadata: null
      outputs: null
      persist: false
      port: 0
      source: null
      workdirectory: ""

    NbMerge:
      Ignore: {}
      attachments: null
      color_words: false
      details: null
      ignore_transients: true
      input_strategy: null
      merge_strategy: "inline"
      metadata: null
      output_strategy: null
      outputs: null
      source: null

    NbMergeWeb:
      Ignore: {}
      attachments: null
      base_url: "/"
      browser: null
      color_words: false
      details: null
      ignore_transients: true
      input_strategy: null
      ip: "127.0.0.1"
      merge_strategy: "inline"
      metadata: null
      output_strategy: null
      outputs: null
      persist: false
      port: 0
      source: null
      workdirectory: ""

    NbShow:
      Ignore: {}
      attachments: null
      details: null
      metadata: null
      outputs: null
      source: null

    Server:
      base_url: "/"
      browser: null
      ip: "127.0.0.1"
      persist: false
      port: 8888
      workdirectory: ""

    Extension:
      Ignore: {}
      attachments: null
      color_words: false
      details: null
      metadata: null
      outputs: null
      source: null

    NbDiffDriver:
      Ignore: {}
      attachments: null
      color_words: false
      details: null
      metadata: null
      outputs: null
      source: null

    NbDiffTool:
      Ignore: {}
      attachments: null
      base_url: "/"
      browser: null
      color_words: false
      details: null
      ip: "127.0.0.1"
      metadata: null
      outputs: null
      persist: false
      port: 0
      source: null
      workdirectory: ""

    NbMergeDriver:
      Ignore: {}
      attachments: null
      color_words: false
      details: null
      ignore_transients: true
      input_strategy: null
      merge_strategy: "inline"
      metadata: null
      output_strategy: null
      outputs: null
      source: null

    NbMergeTool:
      Ignore: {}
      attachments: null
      base_url: "/"
      browser: null
      color_words: false
      details: null
      ignore_transients: true
      input_strategy: null
      ip: "127.0.0.1"
      merge_strategy: "inline"
      metadata: null
      output_strategy: null
      outputs: null
      persist: false
      port: 0
      source: null
      workdirectory: ""




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
    NbDiffTool, Extension).

Merge
    Options to merge commands (NbMerge, NbMergeWeb, NbMergeDriver,
    NbMergeTool).

GitDiff
    Options to git diff commands (NbDiff, NbDiffWeb, NbDiffDriver,
    NbDiffTool, Extension)

GitMerge
    Options to git diff commands (NbMergeDriver, NbMergeTool)


.. note::

    These sections are ways to configure several commands / entrypoints
    at once. The individual command names are the once listed in
    parantheses at the end of the sections, or can be seen by running
    ``nbdime --config``.



Configuring ignores
-------------------

The config system allows for detailed control over what to ignore or not
via the "Ignore" key. It takes a dictionary in the following format::


    "Ignore": {
      "/cells/*/outputs": true,
      "/cells/*/attachments": false,
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
          "/cells/*/outputs": true,
          "/cells/*/metadata": ["collapsed", "autoscroll", "deletable", "editable"]
        }
      }
    }

Here, the final config for a git diff entry point will be::

    {
      "Ignore": {
        "/metadata": ["foo"],
        "/cells/*/outputs": true,
        "/cells/*/metadata": ["collapsed", "autoscroll", "deletable", "editable"]
      }
    }

This means that the "tags" entry from the "Diff" section is not automatically
included in the merge.



Front-end extensions
--------------------

The configuration of the diffing for the front-end extensions (notebook and lab)
is controlled by the section key "Extension". For extensions, nbdime is not
launched as a separate process, but is called as a server extension. For this
reason, any of config options that conflict with those of the lab/notebook
process are ignored.
