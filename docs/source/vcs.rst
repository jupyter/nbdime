===========================
Version control integration
===========================

.. note::

    Currently only integration with git is supported
    out of the box. However, as long as the version 
    control software allows for external drivers 
    and/or tools, integration with nbdime should be
    possible following the same patterns as outlined
    in the manual registration sections.

.. _git-integration:

Git integration
---------------

Git integration of nbdime is supported in two ways:
through *drivers* for diff and merge operations, where
nbdime takes on the responsiblity for performing the
diff/merge; and through defining nbdime as diff and 
merge *tools*, which allow it to display the 
diff/merge to the user without having to actually 
depend on git.

Diff driver
***********
Registering an external diff driver with git tells git
to call that application to calculate and display diffs
to the user. The driver will be called for commands such
as `git diff`, but will not be used for all git commands
(e.g. `git add --patch` will not use the driver).
Consult the git documentation for further details.

Nbdime supplies an entry point for registering its driver
with git::

    git-nbdiffdriver config [--global]

This command will register the nbdime diff driver with 
git on the project (repository) or global (user) level. 
Additionaly, the command will associate the driver with
the ``.ipynb`` file extension, again either on the project
or global level.

Manual registration
^^^^^^^^^^^^^^^^^^^
Alternatively, the diff driver can be registered manually
with the following steps:

- To register the driver with git under the name 
  "jupyternotebook", add the following entries to the 
  appropriate ``.gitconfig`` file::
    
    [diff "jupyternotebook"]
	command = git-nbdiffdriver diff

- To associate the diff driver with a file type,
  add the following entry to the appropriate 
  ``.gitattributes`` file::
    
    *.ipynb	diff=jupyternotebook


Merge driver
************
Registering an external merge driver with git tells git
to call that application to calculate merges of certain
files. This allows nbdime to become responsible for
merging all notebooks.

Nbdime supplies an entry point for registering its merge 
driver with git::

    git-nbmergedriver config [--global]

This command will register the nbdime merge driver with 
git on the project or global level. Additionaly, the 
command will associate the merge driver with the 
``.ipynb`` file extension, again either on the project
or global level.

Manual registration
^^^^^^^^^^^^^^^^^^^
Alternatively, the diff driver can be registered manually
with the following steps:

- To register the driver with git under the name 
  "jupyternotebook", add the following entries to the appropriate 
  ``.gitconfig`` file::
    
    [merge "jupyternotebook"]
	command = git-nbmergedriver merge %O %A %B %L %P

- To associate the diff driver with a file type,
  add the following entry to the appropriate 
  ``.gitattributes`` file::
    
    *.ipynb	diff=jupyternotebook


Diff web tool
*************

The rich, web-based diff view can be installed as a git
*diff tool*. This enables the diff viewer to display diffs
of repository history instead of just files. To register
nbdime as a git diff tool, run the command::
    
    git-nbdifftool config [--global]

Once registered, the diff tool can be started by running
the git command::
    
    git difftool --tool=nbdimeweb [<commit> [<commit>]] [--] [<path>…​]

If you want to avoid specifying the tool each time, nbdime
can be set as the default tool by adding the ``--set-default``
flag to the registration command::
    
    git-nbdifftool config [--global] --set-default

This will set the CLI differ as the default diff tool, and
the web based diff tool as the default GUI diff tool. To 
launch the web view with this configuration, run the
git command as follows::
    
    git difftool -g [<commit> [<commit>]] [--] [<path>…​]

.. note:: 
    Git does not allow to select different tools per file type,
    so if you set nbdime as the default tool it will be called
    for *all changed files*. This includes non-notebooks, which
    nbdime will fail to process.

Manual registration
^^^^^^^^^^^^^^^^^^^

Alternatively, the diff tool can be registered manually
with the following steps:

- To register both the CLI and web diff tools with git under
  the names "nbdime" and "nbdimeweb", add the following entries
  to the appropriate ``.gitconfig`` file::
    
    [difftool "nbdime"]
	cmd = git-nbdifftool diff "$LOCAL" "$REMOTE"
    
    [difftool "nbdimeweb"]
	cmd = git-nbwebdifftool "$LOCAL" "$REMOTE"

- To set the diff tools as the default tools, add or modify
  the following entries in the appropriate``.gitconfig``
  file::
    
    [diff]
    	tool = nbdime
    	guitool = nbdimeweb

Merge web tool
**************

The rich, web-based merge view can be installed as a git
*merge tool*. This enables nbdime to process merge conflicts
during merging in git. To register nbdime as a git 
merge tool, run the command::
    
    git-nbmergetool config [--global]

Once registered, the merge tool can be started by running
the git command::

    git mergetool --tool=nbdimeweb [<file>…​]

If you want to avoid specifying the tool each time, nbdime
can be set as the default tool by adding the ``--set-default``
flag to the registration command::
    
    git-nbmergetool config [--global] --set-default

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
  the name "nbdimeweb", add the following entry
  to the appropriate ``.gitconfig`` file::
    
    [mergetool "nbdimeweb"]
	cmd = git-nbwebmergetool "$LOCAL" "$REMOTE" "$BASE" "$MERGED"

- To set nbdime as the default merge tool, add or modify
  the following entry in the appropriate``.gitconfig``
  file::
    
    [merge]
    	tool = nbdimeweb
