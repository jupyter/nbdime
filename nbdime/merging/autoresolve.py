# coding: utf-8

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import unicode_literals

from six import string_types

from ..diff_format import SequenceDiff, MappingDiff, Diff, make_op
from ..diff_format import as_dict_based_diff, revert_as_dict_based_diff, decompress_sequence_diff
from ..patching import patch


def __find_strategy(path, strategies):
    # Use closest parent strategy if specific entry is missing
    strategy = strategies.get(path)
    ppath = path
    while strategy is None and ppath:
        i = ppath.rfind("/")
        if i >= 0:
            ppath = ppath[:i]
            strategy = strategies.get(path)
        else:
            break
    return strategy


# Strategies for handling conflicts  TODO: Implement these and refine further!
#generic_conflict_strategies = ("mergetool", "use-base", "use-local", "use-remote", "fail")
#source_conflict_strategies = generic_conflict_strategies + ("inline",)
#transient_conflict_strategies = generic_conflict_strategies + ("clear",)
#output_conflict_strategies = transient_conflict_strategies + ("use-all",)


# Sentinel object
Deleted = object()

def __patch_item(value, diffentry):
    op = diffentry.op
    if op == Diff.REPLACE:
        return diffentry.value
    elif op == Diff.PATCH:
        return patch(value, diffentry.diff)
    elif op == Diff.REMOVE:
        return Deleted
    else:
        raise ValueError("Invalid item patch op {}".format(op))

def __make_join_diffentry(value, le, re):
    # Joining e.g. an outputs list means concatenating all items
    lvalue = patch_item(value, le)
    rvalue = patch_item(value, re)

    if lvalue is Deleted:
        lvalue = []
    if rvalue is Deleted:
        rvalue = []
    newvalue = value + lvalue + rvalue
    e = FIXME
    return e

def __make_inline_diffentry(value, le, re):
    # FIXME implement
    e = FIXME
    return e



def cleared_value(value):
    if isinstance(value, list):
        # Clearing e.g. an outputs list means setting it to an empty list
        return []
    elif isinstance(value, dict):
        # Clearing e.g. a metadata dict means setting it to an empty dict
        return {}
    elif isinstance(value, string_types):
        # Clearing e.g. a source string means setting it to an empty string
        return ""
    else:
        # Clearing anything else (atomic values) means setting it to None
        return None


def resolve_single_conflict(value, le, re, strategy, path):
    assert le.key == re.key

    if strategy == "fail":
        raise RuntimeError("Not expecting a conflict at path {}.".format(path))

    elif strategy == "mergetool":
        e, le, re = None, le, re

    elif strategy == "use-base":
        e, le, re = None, None, None

    elif strategy == "use-local":
        e, le, re = le, None, None

    elif strategy == "use-remote":
        e, le, re = re, None, None

    elif strategy == "clear":
        v = cleared_value(value)
        e = make_op(Diff.REPLACE, le.key, v)
        le, re = None, None

    # FIXME: Implement
    #elif strategy == "inline":
    #    e = make_inline_diffentry(value, le, re)
    #    le, re = None

    # FIXME: Implement
    #elif strategy == "join":
    #    e = make_join_diffentry(value, le, re)
    #    le, re = None

    else:
        raise RuntimeError("Invalid strategy {}.".format(strategy))

    return e, le, re


def autoresolve_lists(merged, lcd, rcd, strategies, path):
    key = "*"
    subpath = "/".join((path, key))
    strategy = strategies.get(subpath)

    n = len(merged)
    local = decompress_sequence_diff(lcd, n)
    remote = decompress_sequence_diff(rcd, n)

    resolutions = SequenceDiff()
    newlcd = SequenceDiff()
    newrcd = SequenceDiff()
    for key, value in enumerate(merged):
        # Figure out what lcd and rcd wants to do with merged[key]
        le = local[key]
        re = remote[key]

        assert (le.op == Diff._KEEP) == (re.op == Diff._KEEP)

        if le.op == Diff._KEEP or re.op == Diff._KEEP:
            # Skip items without conflict
            pass
        elif strategy is not None:
            # Autoresolve conflicts for this key
            e, le, re = resolve_single_conflict(value, le, re, strategy, subpath)
            if e is not None:
                resolutions.append(e)
            if le is not None:
                newlcd.append(le)
            if re is not None:
                newrcd.append(re)
        elif le.op == Diff.PATCH and re.op == Diff.PATCH:
            # Recurse if we have no strategy for this key but diffs available for the subdocument
            di, ldi, rdi = autoresolve(value, le.diff, re.diff, strategies, subpath)
            if di:
                resolutions.patch(key, di)
            if ldi:
                newlcd.patch(key, ldi)
            if rdi:
                newrcd.patch(key, rdi)
        else:
            # Alternatives if we don't have PATCH, are:
            #  - INSERT: not happening
            #  - REPLACE: technically possible, if so we can can convert it to PATCH, but does it happen?
            #  - REMOVE: more likely, but resolving subdocument diff will still leave us with a full conflict on parent here
            # No resolution, keep conflicts le, re
            newlcd.append(le)
            newrcd.append(re)

    return resolutions.diff, newlcd.diff, newrcd.diff


def autoresolve_dicts(merged, lcd, rcd, strategies, path):
    # Converting to dict-based diff format for dicts for convenience
    # This step will be unnecessary if we change the diff format to work this way always
    lcd = as_dict_based_diff(lcd)
    rcd = as_dict_based_diff(rcd)

    # We can't have a one-sided conflict so keys must match
    assert set(lcd) == set(rcd)

    resolutions = MappingDiff()
    newlcd = MappingDiff()
    newrcd = MappingDiff()

    for key in sorted(lcd):
        # Query out how to handle conflicts in this part of the document
        subpath = "/".join((path, key))
        strategy = strategies.get(subpath)

        # Get value and conflicts
        value = merged[key]
        le = lcd[key]
        re = rcd[key]
        assert le.key == key
        assert re.key == key

        if strategy is not None:
            # Autoresolve conflicts for this key
            e, le, re = resolve_single_conflict(value, le, re, strategy, subpath)
            if e is not None:
                resolutions.append(e)
            if le is not None:
                newlcd.append(le)
            if re is not None:
                newrcd.append(re)
        elif le.op == Diff.PATCH and re.op == Diff.PATCH:
            # Recurse if we have no strategy for this key but diffs available for the subdocument
            di, ldi, rdi = autoresolve(value, le.diff, re.diff, strategies, subpath)
            if di:
                resolutions.patch(key, di)
            if ldi:
                newlcd.patch(key, ldi)
            if rdi:
                newrcd.patch(key, rdi)
        else:
            # Alternatives if we don't have PATCH, are:
            #  - INSERT: not happening
            #  - REPLACE: technically possible, if so we can can convert it to PATCH, but does it happen?
            #  - REMOVE: more likely, but resolving subdocument diff will still leave us with a full conflict on parent here
            # No resolution, keep conflicts le, re
            newlcd.append(le)
            newrcd.append(re)

    return resolutions.diff, newlcd.diff, newrcd.diff


def autoresolve(merged, local_diff, remote_diff, strategies, path):
    """
    Returns: resolution_diff, unresolved_local_diff, unresolved_remote_diff
    """
    if isinstance(merged, dict):
        return autoresolve_dicts(merged, local_diff, remote_diff, strategies, path)
    elif isinstance(merged, list):
        return autoresolve_lists(merged, local_diff, remote_diff, strategies, path)
    else:
        raise RuntimeError("Invalid merged type {} at path {}".format(type(merged).__name__), path)
