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
git repository or in the home/etc directory for global effect.
Details for how to inidividually configure the different
dirvers/tools are given below.

To configure all diff/merge drivers and tools, simply call::

    nbdime config-git (--enable | --disable) [--global | --system]

This command will register nbdime with git for the current project
(repository), or on the global (user), or sytem level according to
the ``--global`` or ``--system`` options.

.. note::
    When neither the global or system flag is given, the configuration
    is only applied to the current project (repository). The command
    will therefore need to be run from within a git repository.


Usage
*****
Once configured, the diff/merge drivers should simply work out of the
box. For example, the normal git diff command::

    git diff [<commit> [<commit>]] [--] [<path>…​]

should give you the standard diff for any non-notebook files, but
use nbdime's command-line diff for all `.ipynb` files. Nbdime
will also be used for all merges on notebook files (no specific
commands needed).

To launch the rich, web-based tools (for diff visualization and
merge conflict visualization/resolution), the following git
command will need to be executed::

    git difftool --tool nbdime [ref [ref]]

.. figure:: images/nbdiff-web.png
   :alt: example of nbdime's content-aware diff

   Figure: nbdime's content-aware diff

and::

    git mergetool --tool nbdime -- *.ipynb

.. figure:: images/nbmerge-web.png
   :alt: nbdime's merge with web-based GUI viewer

   Figure: nbdime's merge with web-based GUI viewer

.. note::

    Using :command:`git-nbdiffdriver config` overrides the ability to call
    :command:`git difftool` with notebooks.

    You can still call :command:`nbdiff-web` to diff files directly,
    but getting the files from git refs is still on our TODO list.

.. note::

    If you simply call `git mergetool --tool nbdime`, it will be called
    for all merge conflicts, even on filetypes that it cannot handle. To
    only call on notebooks, add a filter on file paths, e.g.
    `git mergetool --tool nbdime -- *.ipynb`. **This command has also been
    aliased as `nbdime mergetool` for easy access**, and you can also add
    your own git alias for this command.


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

    git-nbdiffdriver config --enable [--global | --system]

This command will register the nbdime diff driver with
git, and associate the diff driver with the ``.ipynb``
file extension. The `--global | --system` flags work as
explained above.

Manual registration
^^^^^^^^^^^^^^^^^^^

Alternatively, the diff driver can be registered manually
with the following steps:

- To register the driver with git under the name
  ``"jupyternotebook"``, add the following entries to the
  appropriate ``.gitconfig`` file
  (`git config [--global | --system] -e` to edit)::

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

    git-nbmergedriver config --enable [--global | --system]

This command will register the nbdime merge driver with
git, and associate the merge driver with the ``.ipynb``
file extension. The `--global | --system` flags work as
explained above.

Manual registration
^^^^^^^^^^^^^^^^^^^

Alternatively, the merge driver can be registered manually
with the following steps:

- To register the driver with git under the name
  "jupyternotebook", add the following entries to the appropriate
  ``.gitconfig`` file
  (`git config [--global | --system] -e` to edit)::

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

    git-nbdifftool config --enable [--global | --system]

Once registered, the diff tool can be started by running
the git command::

    git difftool --tool=nbdime [<commit> [<commit>]] [--] [<path>…​]

If you want to avoid specifying the tool each time, nbdime
can be set as the default tool by adding the ``--set-default``
flag to the registration command::

    git-nbdifftool config --enable [--global | --system] --set-default

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
  to the appropriate ``.gitconfig`` file
  (`git config [--global | --system] -e` to edit)::

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
during merging in git, and present them for resolution.

Command line registration
^^^^^^^^^^^^^^^^^^^^^^^^^

To register nbdime as a git merge tool, run the command::

    git-nbmergetool config --enable [--global | --system]

Once registered, the merge tool can be started by running
the git command::

    git mergetool --tool=nbdime [<file>…​]

If you want to avoid specifying the tool each time, nbdime
can be set as the default tool by adding the ``--set-default``
flag to the registration command::

    git-nbmergetool config --enable --set-default [--global | --system]

This will allow the merge tool to be launched simply by::

    git mergetool [<file>…​]

.. note::
    Git does not allow to select different tools per file type,
    so if you set nbdime as the default tool it will be called
    for *all merge conflicts*. This includes non-notebooks, which
    nbdime will fail to process. For most repositories, it will
    therefore not make sense to have nbdime as the default, but
    rather to call it selectively.


Manual registration
^^^^^^^^^^^^^^^^^^^

Alternatively, the merge tool can be registered manually
with the following steps:

- To register both the merge tool with git under
  the name "nbdime", add the following entry
  to the appropriate ``.gitconfig`` file
  (`git config [--global | --system] -e` to edit)::

    [mergetool "nbdime"]
    cmd = git-nbmergetool "$BASE" "$LOCAL" "$REMOTE" "$MERGED"

- To set nbdime as the default merge tool, add or modify
  the following entry in the appropriate ``.gitconfig`` file::

    [merge]
    tool = nbdime
