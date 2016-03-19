Representing merge results and conflicts
========================================

Nbdime implements a three-way merge of Jupyter notebooks and a large
subset of generic JSON objects. The result of a merge operation with a
shared origin object base and modified objects local and remote, is a
fully or partially merged object plus diff objects between the
partially merged objects and the local and remote objects.  These two
diff objects represent the merge conflicts that could not be
automatically resolved.

.. TODO:: Define output formats for the merge operation.


Notebook specific issues
========================

.. TODO:: Document issues covered and plans here.
