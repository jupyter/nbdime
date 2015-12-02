.. nbdime documentation master file, created by
   sphinx-quickstart on Wed Dec  2 12:33:47 2015.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Documentation for nbdime -- tools for diff and merge of Jupyter Notebooks
=========================================================================

NB! The nbdime project and this documentation and is in a very early stage
of development and is not usable for any kind of production work yet.


Contents:

.. toctree::
   :maxdepth: 2



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


Overview
========

In the traditional diff of two sequences X and Y, the diff is a
sequence of transformations turning X into Y.

In nbdime, the objects to diff are json-compatible nested structures
of dicts (limited to string keys) and/or lists of values with
heterogeneous types (strings, ints, floats), warranting a more
flexible diff format. The diff of two objects is still a collection of
transformations, converting one object into the other.

In nbdime there is a single function `nbdiff.patch` that expects an
initial object and a diff object. The expected generic diff format is
defined below. Adhering to this diff format is a number of variations
of diff algorithms for different types of data. The collection of diff
algorithms is under heavy construction and therefore not documented
here yet.

Note that, for all practical purposes, the diff between two objects is
never unique. However any diff must always be correct in the sense
that "patch(X, diff(X, Y)) == Y" holds. This identity is extensively
used in the test suite. The goal of this project is to develop diff
and merge algorithms tailored for Jupyter notebooks that are not only
correct but also have high enough quality to be useful.


A recursive generic diff format
===============================

Note: The diff format herein is considered experimental until
development stabilizes. If you have objections or opinions on
the format, please raise them ASAP while the project is in its
early stages.

The diff is itself a json-compatible object.  Instead of being a
sequence of transformations, it is a tree of transformations, a
hierarchial structure where a transformation may itself contain a
sequence of transformations of a substructure. Each level in the diff
hierarchy applies either to a diff of two dicts, or to a diff of
two sequences (lists or strings). The diff format for dict and
sequence cases are slightly different.

For examples of concrete diffs, see e.g. the test suite for patch.


Diff format for dicts (current)
-------------------------------

A diff of two dicts is a list of diff entries:

    key = string
    entry = [action, key] | [action, key, argument]
    diff = [entry0, entry1, ...]

A dict diff entry is a list of action and argument (except for deletion):

    * ["-", key]: delete value at key
    * ["+", key, newvalue]: insert newvalue at key
    * ["!", key, diff]: patch value at key with diff
    * [":", key, newvalue]: replace value at key with newvalue


Diff format for dicts (alternative)
-----------------------------------

A diff of two dicts is itself a dict mapping string keys to diff entries:

    key = string
    entry = [action] | [action, argument]
    diff = {key0:entry0, key1: entry1, ...}

A dict diff entry is a list of action and argument (except for deletion):

    * ["-"]: delete value at key
    * ["+", newvalue]: insert newvalue at key
    * ["!", diff]: patch value at key with diff
    * [":", newvalue]: replace value at key with newvalue


Diff format for sequences (list and string)
-------------------------------------------

A diff of two sequences is an ordered list of diff entries:

    index = integer
    entry = [action, index] | [action, index, argument]
    diff = [entry0, entry1, ...]

A sequence diff entry is a list of action, index and argument (except for deletion):

    * ["-", index]: delete entry at index
    * ["+", index, newvalue]: insert single newvalue before index
    * ["--", index, n]: delete n entries starting at index
    * ["++", index, newvalues]: insert sequence newvalues before index
    * ["!", index, diff]: patch value at index with diff
    * [":", index, newvalue]: replace value at index with newvalue

Possible simplifications:

    * Remove the ":" action.
    * Remove single-item "-", "+" and rename "--" and "++" to single-letter.
    * OR remove "--" and "++" and stick with just single-item versions.


Representing merge results and conflicts
========================================

TODO: Define output formats for the merge operation.


Notebook specific issues
========================

TODO: Document issues covered and plans here.
