nbdime -- tools for diff and merge of Jupyter Notebooks
=======================================================

In the traditional diff of two sequences X and Y, the diff is a
sequence of transformations turning X into Y.

In nbdime, the objects to diff are json-compatible nested structures
of dicts (limited to string keys) and/or lists of values with
heterogeneous types (strings, ints, floats), warranting a more
flexible diff format. The diff of two objects is still a collection of
transformations, converting one object into the other.

Note that there is almost never a unique diff, but any diff must
always be correct in the sense that "patch(X, diff(X, Y)) == Y"
holds. This identity is extensively used in the test suite.

Below we define a generic diff format. In nbdime there is number of
variations of diff algorithms for different types of data, all of
which adheres to the same diff format. A single function
`nbdiff.patch` can be combined with any diff algorithm.

The collection of diff algorithms is under heavy construction and
therefore not documented.


A recursive generic diff format
-------------------------------

Note: The diff format herein is considered experimental until
development stabilizes.

The diff is itself a json-compatible object.  Instead of being a
sequence of transformations, it is a tree of transformations, a
hierarchial structure where a transformation may itself contain a
sequence of transformations of a substructure.

Each transformation is a list with two or three elements,

   [action, key[, arg]]

where key is a string when referring to a dict, or an int when
referring to a list of string. Action can be one of

    * "-": delete value at key (arg omitted)
    * "+": insert arg at key (if key is list index, just before the item at that index)
    * ":": replace value at key with arg
    * "!": patch value at key with diff=arg

If transforming a sequence (list or string), sequence actions are available:

    * "--": delete arg number of sequence elements starting at key
    * "++": insert sequence arg before element at key

For examples, see e.g. the test suite for patch.
