# coding: utf-8

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import print_function, unicode_literals

from six import string_types
import sys

from ..diff_format import SequenceDiffBuilder, MappingDiffBuilder, DiffOp, offset_op
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
def format_text_merge_display(base, local, remote,
                              base_title="base", local_title="local", remote_title="remote"):
    local = as_text_lines(local)
    base = as_text_lines(base)
    remote = as_text_lines(remote)

    n = 7  # git uses 7
    sep0 = "%s %s\n" % ("<"*n, local_title)
    sep1 = "%s %s\n" % ("="*n, base_title)
    sep2 = "%s %s\n" % ("="*n, remote_title)
    sep3 = "%s\n" % (">"*n,)

    return "".join([sep0] + local + [sep1] + base + [sep2] + remote + [sep3])


# Sentinel object
Deleted = object()


def patch_item(value, diffentry):
    if diffentry is None:
        return value
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


def make_inline_outputs_value(value, le, re,
                              local_title="local", remote_title="remote"):
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


def make_inline_source_value(base, le, re):  # FIXME: Test this!
    if le.op == DiffOp.REPLACE:
        local = le.value
    elif le.op == DiffOp.PATCH:
        local = patch(base, le.diff)
    elif le.op == DiffOp.REMOVE:
        local = []  # ""
    else:
        raise ValueError("Invalid item patch op {}".format(le.op))

    if re.op == DiffOp.REPLACE:
        remote = re.value
    elif re.op == DiffOp.PATCH:
        remote = patch(base, re.diff)
    elif re.op == DiffOp.REMOVE:
        remote = []  # ""
    else:
        raise ValueError("Invalid item patch op {}".format(re.op))

    # FIXME: use format_text_merge_display for each conflicting chunk?
    e = format_text_merge_display(base, local, remote)
    return e


def make_cleared_value(value):
    "Make a new 'cleared' value of the right type."
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


def add_conflicts_record(value, le, re):
    """Add an item 'nbdime-conflicts' to a metadata dict.

    Simply storing metadata conflicts for mergetool inspection.
    """
    assert isinstance(value, dict)
    c = {}
    if le is not None:
        c["local"] = le
    if re is not None:
        c["remote"] = re
    newvalue = dict(value)
    newvalue["nbdime-conflicts"] = c
    return newvalue


def resolve_dict_item_conflict_decision(value, le, re, strategy, path, dec):
    assert le is None or re is None or le.key == re.key
    key = le.key if re is None else re.key

    print('autoresolving conflict at %s with %s' % (path, strategy), file=sys.stderr)

    # Make a shallow copy of dec
    dec = dec.copy()

    # The rest here remove the conflicts and provide a new value
    # ... cases ignoring changes
    if strategy == "clear":
        newvalue = make_cleared_value(value)
        dec["custom_diff"] = op_replace(key, newvalue)
        dec["action"] = "custom"
    elif strategy == "use-base":
        dec["action"] = "base"
    # ... cases ignoring changes from one side
    elif strategy == "use-local":
        dec["action"] = "local"
    elif strategy == "use-remote":
        dec["action"] = "remote"
    # ... cutoffs before cases using changes from both sides
    #  (NB! The position of these elif cases relative to the
    #   cases that check the strategy is important)
    elif le is None:
        # Only one sided change, use that
        dec["action"] = "remote"
        dec["conflict"] = False
    elif re is None:
        # Only one sided change, use that
        dec["action"] = "local"
        dec["conflict"] = False
    elif le == re:
        # Both changes are equal, just apply
        dec["action"] = "either"
        dec["conflict"] = False
    # ... fallthrough
    elif strategy == "mergetool":
        # Leave this type of conflict for external tool to resolve
        pass
    # ... fail
    elif strategy == "fail":
        # Expecting never to get this kind of conflict, raise error
        raise RuntimeError("Not expecting a conflict at path {}.".format(path))
    # ... cases using changes from both sides to produce a new value
    else:
        if strategy == "inline-source":
            newvalue = make_inline_source_value(value, le, re)
        elif strategy == "inline-outputs":
            newvalue = make_inline_outputs_value(value, le, re)
        elif strategy == "join":
            newvalue = make_join_value(value, le, re)
        elif strategy == "record-conflict":
            newvalue = add_conflicts_record(value, le, re)
        else:
            raise RuntimeError("Invalid strategy {}.".format(strategy))
        dec["custom_diff"] = op_replace(key, newvalue)
        dec["action"] = "custom"

    return [dec]


# FIXME: Move to utils
def split_path(path):
    "Split a path on the form /foo/bar into ['foo','bar']."
    return [x for x in path.strip("/").split("/") if x]


def autoresolve_decision_on_dict(dec, base, sub, strategies):
    assert isinstance(sub, dict)

    ld = dec.local_diff
    rd = dec.remote_diff

    # I believe this to be true here
    assert len(ld) == 1 and len(rd) == 1
    assert ld[0].key == rd[0].key

    # Query how to handle conflicts in this part of the document
    key = ld[0].key
    subpath = "/".join((dec.common_path, key))
    strategy = strategies.get(subpath)
    
    # Get value and conflicts
    le, = ld
    re, = rd
    assert le.key == key
    assert re.key == key
    value = sub[key]

    if strategy is not None:
        decs = resolve_dict_item_conflict_decision(value, le, re, strategy, subpath, dec)
    elif le.op == DiffOp.PATCH and re.op == DiffOp.PATCH:
        FIXME # this is not quite right:
        # Recurse if we have no strategy for this key but diffs available for the subdocument
        newdec = dec.copy()
        newdec["common_path"] = "/".join(dec["common_path"], key)
        newdec["local_diff"] = le.diff
        newdec["remote_diff"] = le.diff
        decs = autoresolve_decision(base, newdec, strategies)
    else:
        # Alternatives if we don't have PATCH, are:
        #  - ADD: only happens if inserted values are different,
        #         could possibly autoresolve some cases but nothing important
        #  - REPLACE: technically possible, if so we can can convert it to PATCH,
        #             but does it happen?
        #  - REMOVE: more likely, but resolving subdocument diff will still leave
        #            us with a full conflict on parent here
        # No resolution, keep original decision
        decs = [dec]
    return decs


def autoresolve_decision(base, dec, strategies):
    """Autoresolve a single conflicting decision in isolation.

    Returns a list of 0 or more new decisions, with or without further conflicts.
    """
    assert dec.action == "conflict"

    decs = []

    # Get the non-empty base-local and base-remote diffs
    assert dec.local_diff and dec.remote_diff

    # Query how to handle conflicts in this part of the document
    #strategy = strategies.get(dec.common_path)

    # Get object in base that common_path points to
    sub = base
    for key in split_path(base):
        sub = sub[key]

    if isinstance(sub, dict):
        decs = autoresolve_decision_on_dict(dec, base, sub, strategies)
    elif isinstance(sub, list):
        decs = FIXME
    elif isinstance(sub, string_types):
        decs = FIXME
    else:
        raise RuntimeError("Expecting ")

    return decs


def autoresolve_decisions(base, decisions, strategies):
    """Autoresolve a list of decisions with given strategy configuration.

    Returns a list of new decisions, with or without further conflicts.
    """
    newdecisions = []
    for dec in decisions:
        if dec.action == "conflict":
            newdecisions.extend(autoresolve_decision(base, dec, strategies))
        else:
            newdecisions.append(dec)
    return newdecisions
