================================================
Description of the diff representation in nbdime
================================================

*Note: The diff format herein is still considered experimental until
development stabilizes. If you have objections or opinions on the
format, please raise them ASAP while the project is in its early
stages.*

In nbdime, the objects to diff are json-compatible nested structures
of dicts (with string keys) and lists of values with heterogeneous
types (strings, ints, floats). The difference between these objects
will itself be represented as a json-compatible object in a format
described below.


Diff format basics
------------------

A diff object represents the difference B-A between two objects A and
B as a list of operations (ops) to apply to A to obtain B. Each
operation is represented as a dict with at least two items:

    { "op": <opname>, "key": <key> }

The objects A and B are either mappings (dicts) or sequences (lists or
strings), and a different set of ops are legal for mappings and
sequences. Depending on the op, the operation dict usually contains an
additional argument, documented below.


Diff format for mappings
------------------------

For mappings, the key is always a string. Valid ops are:

    * { "op": "remove",  "key": <string> }
      - delete existing value at key
    * { "op": "add",     "key": <string>, "value": <value> }
      - insert new value at key not previously existing
    * { "op": "replace", "key": <string>, "value": <value> }
      - replace existing value at key with new value
    * { "op": "patch",   "key": <string>, "diff": <diffobject> }
      - patch existing value at key with another diffobject


Diff format for sequences (list and string)
-------------------------------------------

For sequences the key is always an integer index.  This index is
relative to object A of length N.  Valid ops are:

    * { "op": "removerange",  "key": <string>, "length": <n>}
      - delete the values A[key:key+length]
    * { "op": "addrange",     "key": <string>, "values": <values> }
      - insert new items from values list before A[key], at end if key=len(A)
    * { "op": "patch",   "key": <string>, "diff": <diffobject> }
      - patch existing value at key with another diffobject


Relation to JSONPatch
---------------------

The above described diff representation has similarities with the
JSONPatch standard but is different in a few ways. JSONPatch contains
operations "move", "copy", "test" not used by nbdime, and nbdime
contains operations "addrange", "removerange", and "patch" not in
JSONPatch. Instead of providing a recursive "patch" op, JSONPatch uses
a deep JSON pointer based "path" item in each operation instead of the
"key" item nbdime uses. This way JSONPatch can represent the diff
object as a single list instead of the 'tree' of lists that nbdime
uses. To convert a nbdime diff object to the JSONPatch format, use the
function

    from nbdime.diff_format import to_json_patch
    jp = to_json_patch(diff_obj)

Note that this function is currently a draft and not covered by tests.


Examples
--------

For examples of concrete diffs, see e.g. the test suite in test_patch.py.
