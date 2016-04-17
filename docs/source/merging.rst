Merge
=====

Nbdime implements a three-way merge of Jupyter notebooks and a
subset of generic JSON objects.

Results
-------

A merge operation with a shared origin object base and modified
objects, local and remote, output these **merge results**:

- a fully or partially merged object
- diff objects between the partially merged objects and the local and
  remote objects.

Conflicts
---------

These two diff objects represent the **merge conflicts** that could not be
automatically resolved.

.. TODO:: Define output formats for the merge operation.
