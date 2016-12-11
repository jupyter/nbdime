===========================
Version control integration
===========================

.. note::

    Currently only integration with git is supported
    out of the box.

    Integration with other version control software
    should be possible if the version control software
    allows for external drivers and/or tools. For integration,
    follow the same patterns as outlined
    in the manual registration sections.

.. _git-integration:

Git integration
---------------

Git integration of nbdime is supported in two ways:

- through **drivers** for diff and merge operations, where
  nbdime takes on the responsibility for performing the
  diff/merge:

      * `Diff driver`_
      * `Merge driver`_

- through defining nbdime as diff and
  merge **tools**, which allow nbdime to display the
  diff/merge to the user without having to actually
  depend on git:

      * `Diff web tool`_
      * `Merge web tool`_

Configure git integration by editing the ``.gitconfig``
(or ``.git/config``) and ``.gitattributes`` in each
git repository or in the home directory for global effect.
Read on for commands that edit these files
and execute nbdime through git.

Diff driver
***********

Registering an external diff driver with git tells git
to call that application to calculate and display diffs
to the user. The driver will be called for commands such
as :command:`git diff`, but will not be used for all git commands
(e.g. :command:`git add --patch` will not use the driver).
Consult the git documentation for further details.

Registration can be done in two ways -- at the command line or manually.

Command line registration
^^^^^^^^^^^^^^^^^^^^^^^^^

nbdime supplies an entry point for registering its driver
with git::

    git-nbdiffdriver config --enable [--global]

This command will register the nbdime diff driver with 
git on the project (repository) or global (user) level
when the ``--global`` option is used.
Additionally, this command will associate the diff driver with
the ``.ipynb`` file extension, again either on the project
or global level.

Manual registration
^^^^^^^^^^^^^^^^^^^

Alternatively, the diff driver can be registered manually
with the following steps:

- To register the driver with git under the name 
  ``"jupyternotebook"``, add the following entries to the
  appropriate ``.gitconfig`` file::

    [diff "jupyternotebook"]
    command = git-nbdiffdriver diff

- To associate the diff driver with a file type,
  add the following entry to the appropriate 
  ``.gitattributes`` file::

    *.ipynb diff=jupyternotebook


Merge driver
************

Registering an external merge driver with git tells git
to call that driver application to calculate merges of certain
files. This allows nbdime to become responsible for
merging all notebooks.

Registration can be done in two ways -- at the command line or manually.

Command line registration
^^^^^^^^^^^^^^^^^^^^^^^^^

nbdime supplies an entry point for registering its merge 
driver with git::

    git-nbmergedriver config --enable [--global]

This command will register the nbdime merge driver with 
git on the project or global level. Additionaly, the 
command will associate the merge driver with the 
``.ipynb`` file extension, again either on the project
or global level.

Manual registration
^^^^^^^^^^^^^^^^^^^

Alternatively, the merge driver can be registered manually
with the following steps:

- To register the driver with git under the name 
  "jupyternotebook", add the following entries to the appropriate 
  ``.gitconfig`` file::

    [merge "jupyternotebook"]
    command = git-nbmergedriver merge %O %A %B %L %P

- To associate the merge driver with a file type,
  add the following entry to the appropriate 
  ``.gitattributes`` file::
    
    *.ipynb merge=jupyternotebook


Diff web tool
*************

The rich, web-based diff view can be installed as a git
*diff tool*. This enables the diff viewer to display diffs
of repository history instead of just files.

Command line registration
^^^^^^^^^^^^^^^^^^^^^^^^^

To register nbdime as a git diff tool, run the command::

    git-nbdifftool config --enable [--global]

Once registered, the diff tool can be started by running
the git command::

    git difftool --tool=nbdime [<commit> [<commit>]] [--] [<path>…​]

If you want to avoid specifying the tool each time, nbdime
can be set as the default tool by adding the ``--set-default``
flag to the registration command::

    git-nbdifftool config --enable [--global] --set-default

This command will set the CLI's diff tool as the default diff tool, and
the web based diff tool as the default GUI diff tool. To 
launch the web view with this configuration, run the
git command as follows::

    git difftool -g [<commit> [<commit>]] [--] [<path>…​]

.. note::

    Git does not allow selection of different tools per file type.
    If you set nbdime as the default tool it will be called
    for **all** changed files. This includes non-notebook files, which
    nbdime will fail to process.

Manual registration
^^^^^^^^^^^^^^^^^^^

Alternatively, the diff tool can be registered manually
with the following steps:

- To register both the CLI and web diff tools with git under
  the names "nbdime" and "nbdime", add the following entries
  to the appropriate ``.gitconfig`` file::

    [difftool "nbdime"]
    cmd = git-nbdifftool diff "$LOCAL" "$REMOTE"
    
    [difftool "nbdime"]
    cmd = git-nbdifftool "$LOCAL" "$REMOTE"

- To set the diff tools as the default tools, add or modify
  the following entries in the appropriate``.gitconfig`` file::
    
    [diff]
    tool = nbdime
    guitool = nbdime

Merge web tool
**************

The rich, web-based merge view can be installed as a git
*merge tool*. This enables nbdime to process merge conflicts
during merging in git.

Command line registration
^^^^^^^^^^^^^^^^^^^^^^^^^

To register nbdime as a git merge tool, run the command::

    git-nbmergetool config --enable [--global]

Once registered, the merge tool can be started by running
the git command::

    git mergetool --tool=nbdime [<file>…​]

If you want to avoid specifying the tool each time, nbdime
can be set as the default tool by adding the ``--set-default``
flag to the registration command::

    git-nbmergetool config --enable --set-default [--global]

This will allow the merge tool to be launched simply by::

    git mergetool [<file>…​]

.. note:: 
    Git does not allow to select different tools per file type,
    so if you set nbdime as the default tool it will be called
    for *all merge conflicts*. This includes non-notebooks, which
    nbdime will fail to process. For most repositories, it will
    therefore not make sense to have nbdime as the default, but
    rather to call it selectively 


Manual registration
^^^^^^^^^^^^^^^^^^^

Alternatively, the merge tool can be registered manually
with the following steps:

- To register both the merge tool with git under
  the name "nbdime", add the following entry
  to the appropriate ``.gitconfig`` file::

    [mergetool "nbdime"]
    cmd = git-nbmergetool "$BASE" "$LOCAL" "$REMOTE" "$MERGED"

- To set nbdime as the default merge tool, add or modify
  the following entry in the appropriate ``.gitconfig`` file::

    [merge]
    tool = nbdime
