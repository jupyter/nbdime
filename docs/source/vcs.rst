===========================
Version control integration
===========================

.. note::

    Currently only integration with git is supported
    out of the box. However, as long as the version 
    control software allows for external drivers 
    and/or tools, integration with nbdime should be
    possible following the same patterns as outlined
    here.

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
************
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
  "jupyternotebook",add the following entries to the 
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
