================================================
Description of the diff representation in nbdime
================================================

.. note::

   The diff format herein is still considered experimental until
   development stabilizes. If you have objections or opinions on the
   format, please raise them ASAP while the project is in its early
   stages.

In nbdime, the objects to diff are:

   - json-compatible nested structures of dicts (with string keys) and
   - lists of values with heterogeneous types (strings, ints, floats).

The difference between these objects will itself be represented as a
json-compatible object in a format described below.

Diff format basics
------------------

A diff object represents the difference B-A between two objects A and
B as a list of operations (ops) to apply to A to obtain B. Each
operation is represented as a dict with at least two items::

    { "op": <opname>, "key": <key> }

The objects A and B are either mappings (dicts) or sequences (lists or
strings). A different set of ops are legal for mappings and sequences.
Depending on the op, the operation dict usually contains an additional
argument, as documented below.

Diff format for mappings
------------------------

For mappings, the key is always a string. Valid ops are:

    * "remove" - delete existing value at ``key``::

        { "op": "remove", "key": <string> }

    * "add" - insert new value at ``key`` not previously existing::

        { "op": "add", "key": <string>, "value": <value> }

    * "replace" - replace existing value at ``key`` with new value::

        { "op": "replace", "key": <string>, "value": <value> }

    * "patch" - patch existing value at ``key`` with another ``diffobject``::

        { "op": "patch", "key": <string>, "diff": <diffobject> }

Diff format for sequences (list and string)
-------------------------------------------

For sequences the key is always an integer index.  This index is
relative to object A of length N.  Valid ops are:

    * "removerange" - delete the values ``A[key:key+length]``::

        { "op": "removerange", "key": <string>, "length": <n>}

    * "addrange" - insert new items from ``valuelist`` before ``A[key]``, at end if ``key=len(A)``::

        { "op": "addrange", "key": <string>, "valuelist": <values> }

    * "patch" - patch existing value at ``key`` with another ``diffobject``::

        { "op": "patch",   "key": <string>, "diff": <diffobject> }

Relation to JSONPatch
---------------------

The above described diff representation has similarities with the
JSONPatch standard but is also different in a few ways. JSONPatch contains
operations "move", "copy", "test" not used by nbdime, and nbdime
contains operations "addrange", "removerange", and "patch" not in
JSONPatch. Instead of providing a recursive "patch" op, JSONPatch uses
a deep JSON pointer based "path" item in each operation instead of the
"key" item nbdime uses. This way JSONPatch can represent the diff
object as a single list instead of the 'tree' of lists that nbdime
uses. To convert a nbdime diff object to the JSONPatch format, use the
function::

    from nbdime.diff_format import to_json_patch
    jp = to_json_patch(diff_obj)

.. note::

   This function is currently a draft and not covered by tests.

Examples
--------

For examples of diffs using nbdime, see e.g. the test suite in
``test_patch.py``.
