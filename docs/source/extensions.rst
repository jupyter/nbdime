===================
Notebook Extensions
===================

Installation
============

To install and enable the nbdime notebook extensions, run::

    nbdime reg-extensions [--sys-prefix/--user/--system]

Or, if you prefer full control, you can run the individual steps::

    jupyter serverextension enable --py nbdime [--sys-prefix/--user/--system]

    jupyter nbextension install --py nbdime [--sys-prefix/--user/--system]
    jupyter nbextension enable --py nbdime [--sys-prefix/--user/--system]

This will install the nbdime notebook server extension, and the notebook
frontend extension.


Usage
=====

After installing the extensions, one or two buttons should show up in the
notebook toolbar, as shown in the figure below.

.. figure:: images/nbext-preview.png
   :alt: nbdime buttons in notebook extension

   Figure: nbdime's buttons in the notebook extension.

Clicking the git button will open a new tab showing the diff between the
the last commit and the *currently saved* version of the notebook. Note that
this button will only be visible if the notebook is currently in a git
repository.

Clicking the checkpoint button will similarly show the diff between the
*checkpointed* and *currently saved* versions of the notebook.
