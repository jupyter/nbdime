# coding: utf-8

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

import itertools
import copy

from .diff_format import DiffOp, DiffEntry, op_addrange, op_removerange
from .log import NBDiffFormatError


_addops = (DiffOp.ADD, DiffOp.ADDRANGE)


if hasattr(itertools, "accumulate"):
    _accum = itertools.accumulate
else:
    def _accum(seq):
        total = 0
        for x in seq:
            total += x
            yield total


def offset_op(e, n):
    """Recreate sequence diff entry with offset added to key."""
    e = DiffEntry(e)
    e.key += n
    return e


def count_consumed_symbols(e):
    """Count how many symbols are consumed from each sequence by a single sequence diff entry."""
    op = e.op
    if op == DiffOp.ADDRANGE:
        return (0, len(e.valuelist))
    elif op == DiffOp.REMOVERANGE:
        return (e.length, 0)
    elif op == DiffOp.PATCH:
        return (1, 1)
    else:
        raise NBDiffFormatError("Invalid op '{}'".format(op))


def source_as_string(source):
    """Return source as a single string, joined as lines if it's a list."""
    if isinstance(source, list):
        source = "\n".join(line.strip("\n") for line in source)
    if not isinstance(source, str):
        raise TypeError("Invalid argument type. Should be string or sequence of strings."
                        "Got %r" % source)
    return source


def _overlaps(existing, new):
    """Check whether existing diff op shares a key with the new diffop, and if
    they also have the same op type.
    """
    if not existing:
        return False
    existing = existing[-1]  # Only need to check last op!
    if existing.op == new.op:
        if existing.key == new.key:
            # Found a match, combine ops
            return True
        elif (existing.op == DiffOp.REMOVERANGE and
              existing.key + existing.length >= new.key):
            # Overlapping deletes
            # Above check is open ended to allow sanity check here:
            if existing.key + existing.length != new.key:
                raise RuntimeError('Unexpected diff keys/lengths')
            return True
    elif (existing.op in _addops and
          new.op in _addops and
          existing.key == new.key):
        # Addrange and single add can both point to same key
        return True
    return False


def _combine_ops(existing, new):
    """Combines two ops into a new one that does the same
    """
    if new.op in _addops:
        if existing.op == DiffOp.ADD:
            # Convert to range for compatibility
            d = op_addrange(existing.key, [existing.value])
        else:
            d = copy.deepcopy(existing)
        if new.op == DiffOp.ADDRANGE:
            d.valuelist += new.valuelist
        else:
            if isinstance(d.valuelist, str):
                d.valuelist += new.value
            else:
                d.valuelist.append(new.value)
        return d
    elif new.op == DiffOp.REMOVERANGE:
        assert existing.op == DiffOp.REMOVERANGE, "Unexpect diff op. Invalid use of _combine_ops"
        return op_removerange(existing.key, existing.length + new.length)


def flatten_list_of_string_diff(a, linebased_diff):
    """Translates a diff of strings split by str.splitlines(True) to a diff of
    the joined multiline string.
    """
    if isinstance(a, str):
        a = a.splitlines(True)

    line_to_char = [0] + list(_accum(len(ia) for ia in a))
    charbased_diff = []
    for e in linebased_diff:
        op = e.op
        line_offset = line_to_char[e.key]
        if op == DiffOp.PATCH:
            # For patches, each entry applies to chars within a line,
            # and will have keys (=char indices) relative to line start,
            # so we simply need to offset each key with line offset
            for p in e.diff:
                d = copy.deepcopy(p)
                d.key += line_offset
                charbased_diff.append(d)
        else:
            # Other ops simply have keys which refer to lines
            if op == DiffOp.ADDRANGE:
                d = op_addrange(line_offset, "".join(e.valuelist))
            elif op == DiffOp.REMOVERANGE:
                d = op_removerange(
                    line_offset, line_to_char[e.key + e.length] - line_offset)
            else:
                # Other ops simply need to adjust key as add/replace's value
                # will already be a string
                d = copy.deepcopy(e)
                d.key = line_offset
            charbased_diff.append(d)

    # Combine overlapping diffs
    combined = []
    for d in charbased_diff:
        # If it overlaps with an existing op, combine them to one
        if _overlaps(combined, d):
            combined[-1] = _combine_ops(combined[-1], d)
        else:
            combined.append(d)

    combined.sort(key=lambda x: x.key)
    return combined


def to_clean_dicts(di):
    "Recursively convert dict-like objects to straight python dicts."
    if isinstance(di, dict):
        return {k: to_clean_dicts(v) for k, v in di.items()}
    elif isinstance(di, list):
        return [to_clean_dicts(v) for v in di]
    else:
        return di


def to_diffentry_dicts(di):  # TODO: Better name, validate_diff? as_diff?
    "Recursively convert dict objects to DiffEntry objects with attribute access."
    if isinstance(di, dict):
        return DiffEntry(**{k: to_diffentry_dicts(v) for k, v in di.items()})
    elif isinstance(di, list):
        return [to_diffentry_dicts(v) for v in di]
    else:
        return di

def as_dict_based_diff(di):
    """Converting to dict-based diff format for dicts for convenience.

    NB! Only one level, not recursive.

    This step will be unnecessary if we change the diff format to work this way always.
    """
    return {e.key: e for e in di}


def revert_as_dict_based_diff(di):
    "Reverts as_dict_based_diff."
    return [di[k] for k in sorted(di)]


def to_json_patch(d, path=""):
    """Convert nbdime diff object into the RFC6902 JSON Patch format.

    This is untested and will need some details worked out.
    """
    print("Warning: to_json_patch is not thouroughly tested.")
    jp = []
    offset = 0
    for e in d:
        op = e.op
        if op == DiffOp.ADD:
            assert isinstance(e.key, str), "'add' diff op needs string key"
            p = "/".join([path, e.key])
            jp.append({"op": "add", "path": p, "value": e.value})
        elif op == DiffOp.REPLACE:
            assert isinstance(e.key, str), "'replace' diff op needs string key"
            p = "/".join([path, e.key])
            jp.append({"op": "replace", "path": p, "value": e.value})
        elif op == DiffOp.REMOVE:
            assert isinstance(e.key, str), "'remove' diff op needs string key"
            p = "/".join([path, e.key])
            jp.append({"op": "remove", "path": p})
        elif op == DiffOp.ADDRANGE:
            # JSONPatch only has single value add, no addrange,
            # repeat addition after increasing index instead
            assert isinstance(e.key, int), "'addrange' diff op needs integer key"
            for value in e.valuelist:
                p = "/".join([path, str(e.key + offset)])
                jp.append({"op": "add", "path": p, "value": value})
                offset += 1
        elif op == DiffOp.REMOVERANGE:
            assert isinstance(e.key, int), "'removerange' diff op needs integer key"
            # JSONPatch only has single value remove, no removerange,
            # repeat removal at same index instead
            p = "/".join((path, str(e.key + offset)))
            for _ in range(e.length):
                jp.append({"op": "remove", "path": p})
                offset -= 1
        elif op == DiffOp.PATCH:
            # JSONPatch has no recursion, recurse here to flatten diff
            key = e.key
            if isinstance(key, int):
                key += offset
            p = "/".join([path, str(key)])
            jp.extend(to_json_patch(e.diff, p))
    return jp
