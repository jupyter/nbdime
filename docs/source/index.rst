.. nbdime documentation master file, created by
   sphinx-quickstart on Wed Dec  2 12:33:47 2015.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

nbdime -- diffing and merging of Jupyter Notebooks
==================================================

Version: |version|

Abstract
--------

**nbdime** provides tools for diffing and merging `Jupyter notebooks <jupyter-notebook>`_.
Notebooks are great, rich media documents stored in a plain text JSON format.
This is relatively easy to parse, but primitive line-based diff and merge tools
do not understand the structure of notebook documents, and do not behave well,
yielding diffs like this:

TODO: screenshot of bad line-based diff.

nbdime, on the other hand, understands notebook documents,
and can make intelligent decisions when diffing and merging notebooks,
such as:

- eliding base64-encoded images for terminal output
- use existing diff tools for inputs and outputs
- render image diffs in a web view
- auto-resolve conflicts on generated values such as execution counters



Quickstart
----------

To get started with nbdime, install with pip::

    pip install nbdime

And you can be off to the races diffing notebooks in your terminal with::

    nbdiff notebook-1.ipynb notebook-2.ipynb

or viewing a rich web-based rendering of the diff with::

    nbdiff-web notebook-1.ipynb notebook-2.ipynb

For more on how you can use nbdime, see :doc:`cli`.

Git quickstart
**************

Many of us writing and sharing notebooks do so with git and GitHub.
Git doesn't handle diffing and merging notebooks very well by default,
but you can tell git to use nbdime and it will get a lot better.

To tell git to use nbdime to as a command-line driver to diff and merge notebooks::

    git-nbdiffdriver config --enable --global
    git-nbmergedriver config --enable --global

Now when you do :command:`git diff` or :command:`git merge` and notebooks are involved,
you should see a nice diff view, like this:

TODO: screenshot

To tell git to use the web-based GUI viewers of notebook diffs and merges::

    git-nbdifftool config --enable --global
    git-nbmergetool config --enable --global

With these, you can trigger the :command:`tools` with::

    git difftool --tool nbdime [ref [ref]]

TODO: screenshot of diff-web

and

    git mergetool --tool nbdime

TODO: screenshot of merge-web


.. note::

    :command:`git diffdriver` config overrides the ability to call :command:`git difftool` with notebooks.
    You can still call `nbdiff-web` to diff files directly,
    but getting those files from git refs is still on our TODO list.

For more detailed information on integrating nbdime with version control, see :doc:`vcs`.

Contents
--------
.. toctree::
   :maxdepth: 2
   :caption: Installation and usage

   installing
   cli
   vcs
   testing
   glossary

.. toctree::
   :maxdepth: 2
   :caption: Planning

   usecases
   diffing
   merging
   restapi.md


.. links

.. jupyter-notebook: https://jupyter-notebook.readthedocs.io
