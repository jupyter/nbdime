Merge
=====

Nbdime implements a three-way merge of Jupyter notebooks and a
subset of generic JSON objects.

Results
-------

A merge operation with a shared origin object base and modified
objects, local and remote, output these **merge results**:

- a fully or partially merged object
- a set of merge decision objects that describe the merge operation

Conflicts
---------

Each merge decision has a `conflict` flag indicating a **merge conflict**
that could not be automatically resolved.

Merge decision format
---------------------

Each three-way notebook merge is based on the differences between the base
version and the two changed versions -- **local** and **remote**. These
differences are then compared, and for each change a set of decisions are
made. A :term:`merge decision` object represents such a decision, and is
represented as a dict with the following entries::

    {
        "local_diff": <:term:`diff object`>,
        "remote_diff": <:term:`diff object`>,
        "conflict": <boolean>,
        "action": <action taken/suggested>,
        "common_path": <JSON path>,
        "custom_diff": <:term:`diff object`>
    }

Merge conflicts
***************
Merge conflicts are indicated with the `conflict` field on the decision
object, and if true, indicates that the given differences could not be
automatically reconciled.

.. note::

    Even when conflicted, the `action` field might indicate a suggested
    or "best guess" resolution of the decision. If no such suggestion
    can be inferred, it will default to using the base value.

Merge actions
*************
Each :term:`merge decision` has an entry `action` which describes the
resolution of the merge. It can take the following values:

    - **local** - Use the local changes, as decribed by `local_diff`.
    - **remote** - Use the remote changes as decribed by `remote_diff`.
    - **base** - Use the original value.
    - **either** - Indicates that the local and remote changes are
      interchangeable, and that either can be used.
    - **local\_then\_remote** - First apply the local changes, then the
      remote changes. This is only applicable for certain subset of
      merges, like insertions in the same location (for example two
      cells added in the same location).
    - **remote\_then\_local** - Similar to `local\_then\_remote`, but
      remote changes are taken before local ones.
    - **clear** - Remove the value(s) on the object. For example to
      clear the outputs of a cell.
    - **custom** - Use the changes as decsribed by `custom_diff`.
      This can be used for more complex resolutions than those described
      by the other actions above. A simple example would be for the case
      of multiple cells (or alternatively lines of text) inserted both
      locally and remotely in the same location. Here, the correct
      resolution might be to take the first element from local, then
      the remote changes, and finally the rest of the local changes.

Common path
***********
The `common_path` entry of a merge decision describes the path in which
the local and remote changes diverge. For example if the local changes
are specified as::

    patch "cells"
    ┗━┓ patch index 0
      ┣━┓ patch "source"
      ┃ ┗━ addrange <some lines of source to add>
      ┗━┓ patch "outputs"
        ┗━ addrange <a new output added>

and the remote changes are specified as::

    patch "cells"
    ┗━┓ patch index 0
      ┗━┓ patch "outputs"
        ┗━ removerange <all outputs removed>

then the common path will be `["cells", 0]`, and the :term:`diff objects`
will omit the `patch "cells"` and `patch 0` operations.
