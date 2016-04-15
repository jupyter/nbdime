# coding: utf-8

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import unicode_literals

from six import string_types

from ..diff_format import SequenceDiffBuilder, MappingDiffBuilder, DiffOp, op_replace
from ..diff_format import as_dict_based_diff
from ..patching import patch
from .chunks import make_merge_chunks


# FIXME: Move to utils
def as_text_lines(text):
    if isinstance(text, string_types):
        text = text.splitlines(True)
    if isinstance(text, tuple):
        text = list(text)
    assert isinstance(text, list)
    assert all(isinstance(t, string_types) for t in text)
    return text

# FIXME: Move to utils
def format_text_merge_display(local, remote,
                              local_title="local", remote_title="remote"):
    local = as_text_lines(local)
    remote = as_text_lines(remote)

    n = 7  # git uses 7
    pre = "%s %s" % ("<"*n, local_title)
    mid = "="*n
    post = "%s %s" % (">"*n, remote_title)

    return "\n".join([pre] + local + [mid] + remote + [post])


# Sentinel object
Deleted = object()

def patch_item(value, diffentry):
    op = diffentry.op
    if op == DiffOp.REPLACE:
        return diffentry.value
    elif op == DiffOp.PATCH:
        return patch(value, diffentry.diff)
    elif op == DiffOp.REMOVE:
        return Deleted
    else:
        raise ValueError("Invalid item patch op {}".format(op))


def make_join_value(value, le, re):
    # Joining e.g. an outputs list means concatenating all items
    lvalue = patch_item(value, le)
    rvalue = patch_item(value, re)

    if lvalue is Deleted:
        lvalue = []
    if rvalue is Deleted:
        rvalue = []

    # New list
    newvalue = value + lvalue + rvalue

    return newvalue


def make_inline_outputs_value(value, le, re):
    # FIXME: Use this for inline outputs diff?
    # Joining e.g. an outputs list means concatenating all items
    lvalue = patch_item(value, le)
    rvalue = patch_item(value, re)

    if lvalue is Deleted:
        lvalue = []
    if rvalue is Deleted:
        rvalue = []

    # Note: This is very notebook specific while the rest of this file is more generic
    newvalue = (
        [{"output_type": "stream", "name": "stderr", "text": ["<"*7 + local_title]}]
        + lvalue
        + [{"output_type": "stream", "name": "stderr", "text": ["="*7]}]
        + rvalue
        + [{"output_type": "stream", "name": "stderr", "text": ["<"*7 + remote_title]}]
        )

    return newvalue


def make_inline_source_value(value, le, re):  # FIXME: Test this!
    if le.op == DiffOp.REPLACE:
        local = le.value
    elif le.op == DiffOp.PATCH:
        local = patch(value, le.diff)
    elif le.op == DiffOp.REMOVE:
        local = []  # ""
    else:
        raise ValueError("Invalid item patch op {}".format(le.op))

    if re.op == DiffOp.REPLACE:
        remote = re.value
    elif re.op == DiffOp.PATCH:
        remote = patch(value, re.diff)
    elif re.op == DiffOp.REMOVE:
        remote = []  # ""
    else:
        raise ValueError("Invalid item patch op {}".format(re.op))

    # FIXME: use format_text_merge_display for each conflicting chunk
    e = format_text_merge_display(local, remote)
    return e


def make_cleared_value(value):
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
        v = make_cleared_value(value)
        e = op_replace(le.key, v)
        le, re = None, None

    elif strategy == "inline-source":
        v = make_inline_source_value(value, le, re)
        e = op_replace(le.key, v)
        le, re = None, None

    elif strategy == "inline-outputs":
        v = make_inline_outputs_value(value, le, re)
        e = op_replace(le.key, v)
        le, re = None, None

    elif strategy == "join":
        v = make_join_value(value, le, re)
        e = op_replace(le.key, v)
        le, re = None, None

    else:
        raise RuntimeError("Invalid strategy {}.".format(strategy))

    return e, le, re


def autoresolve_lists(merged, lcd, rcd, strategies, path):
    key = "*"
    subpath = "/".join((path, key))
    strategy = strategies.get(subpath)

    # Cutting off handling of strategies of subitems if there's a strategy for these list items
    if strategy is None:
        pass  # Go on and potentially recurse
    elif strategy == "mergetool":
        return [], lcd, rcd
    elif strategy == "use-base":
        return [], [], []
    elif strategy == "use-local":
        return lcd, [], []
    elif strategy == "use-remote":
        return rcd, [], []
    # I think these don't make sense for list items? Applied to lists instead?
    #elif strategy == "clear":
    #elif strategy == "inline"
    #elif strategy == "join":
    elif strategy == "fail":
        raise RuntimeError("Not expecting a conflict at path {}.".format(path))
    else:
        raise RuntimeError("Not expecting strategy {} for list items at path {}.".format(strategy, path))

    # Data structures for storing conflicts
    resolutions = SequenceDiffBuilder()
    newlcd = SequenceDiffBuilder()
    newrcd = SequenceDiffBuilder()

    # Offset of indices between merged and resolved
    merged_offset = 0

    # Split up and combine diffs into chunks [(begin, end, localdiffs, remotediffs)]
    chunks = make_merge_chunks(merged, lcd, rcd)

    # Loop over chunks of base[j:k], grouping insertion at j into
    # the chunk starting with j
    for (j, k, d0, d1) in chunks:
        # Skip chunks with no conflict
        if not (d0 or d1):
            continue

        linserts = [e for e in d0 if e.op == DiffOp.ADDRANGE]
        rinserts = [e for e in d1 if e.op == DiffOp.ADDRANGE]
        lpatches = [e for e in d0 if e.op == DiffOp.PATCH]
        rpatches = [e for e in d1 if e.op == DiffOp.PATCH]

        if lpatches and rpatches:
            assert len(lpatches) == 1
            assert len(rpatches) == 1
            assert len(lpatches) + len(linserts) == len(d0)
            assert len(rpatches) + len(rinserts) == len(d1)
            assert k == j + 1
            assert all(e.key == j for e in linserts + rinserts)
            le, = lpatches
            re, = rpatches
            # Recurse if we have diffs available for both subdocuments
            di, ldi, rdi = autoresolve(merged[j], le.diff, re.diff, strategies, subpath)

            # NB! Possibly contentious handling of inserts here:
            # if patch conflicts have been resolved, allow inserts from both sides
            if not (ldi or rdi):
                for e in linserts + rinserts:
                    resolutions.append(e)
            else:
                for e in linserts:
                    newlcd.append(e)
                for e in rinserts:
                    newrcd.append(e)

            # Now add patch entries with result of autoresolve recursion
            if di:
                resolutions.patch(j, di)
            if ldi:
                newlcd.patch(j, ldi)
            if rdi:
                newrcd.patch(j, rdi)
        else:
            # Alternatives if we don't have PATCH, are:
            #  - INSERT: not happening
            #  - REPLACE: technically possible, if so we can can convert it to PATCH, but does it happen?
            #  - REMOVE: more likely, but resolving subdocument diff will still leave us with a full conflict on parent here
            # No resolution, keep conflicts le, re
            for e in d0:
                newlcd.append(e)  # offset_op(e, merged_offset))
            for e in d1:
                newrcd.append(e)  # offset_op(e, merged_offset))

    return resolutions.validated(), newlcd.validated(), newrcd.validated()


def autoresolve_dicts(merged, lcd, rcd, strategies, path):
    # Converting to dict-based diff format for dicts for convenience
    # This step will be unnecessary if we change the diff format to work this way always
    lcd = as_dict_based_diff(lcd)
    rcd = as_dict_based_diff(rcd)

    # We can't have a one-sided conflict so keys must match
    assert set(lcd) == set(rcd)

    resolutions = MappingDiffBuilder()
    newlcd = MappingDiffBuilder()
    newrcd = MappingDiffBuilder()

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

        elif le.op == DiffOp.PATCH and re.op == DiffOp.PATCH:
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
            #  - INSERT: only happens if inserted values are different, could possibly autoresolve some cases but nothing important
            #  - REPLACE: technically possible, if so we can can convert it to PATCH, but does it happen?
            #  - REMOVE: more likely, but resolving subdocument diff will still leave us with a full conflict on parent here
            # No resolution, keep conflicts le, re
            newlcd.append(le)
            newrcd.append(re)

    return resolutions.validated(), newlcd.validated(), newrcd.validated()


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
