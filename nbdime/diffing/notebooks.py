# coding: utf-8

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

"""Tools for diffing notebooks.

All diff tools here currently assumes the notebooks have already been
converted to the same format version, currently v4 at time of writing.
Up- and down-conversion is handled by nbformat.
"""

import operator
import re
import copy
from functools import lru_cache

from ..diff_format import MappingDiffBuilder, DiffOp
from ..utils import defaultdict2

from .config import DiffConfig
from .generic import (
    diff, diff_sequence_multilevel, compare_strings_approximate,
    diff_string_lines,
)

__all__ = ["diff_notebooks"]

# A regexp matching base64 encoded data
_base64 = re.compile(r'^(?:[a-z0-9+/]{4})*(?:[a-z0-9+/]{2}==|[a-z0-9+/]{3}=)?$', re.UNICODE | re.IGNORECASE)

# A regexp matching common python repr-style output like
# <module.type at 0xmemoryaddress>
re_repr = re.compile(r"<[a-z0-9._]+ at 0x[a-f0-9]{8,16}>", re.IGNORECASE)

re_pointer = re.compile(r"0x[a-f0-9]{8,16}", re.IGNORECASE)

TEXT_MIMEDATA_MAX_COMPARE_LENGTH = 10000
STREAM_MAX_COMPARE_LENGTH = 1000


# List of mimes we can diff recursively
_split_mimes = (
    'text/',
    'image/svg+xml',
    'application/javascript',
    'application/json',
    )


def _is_base64(test_string, min_len=64):
    """Whether string is base64 data, possibly with newlines in it"""
    if len(test_string) < min_len:
        return False
    return _base64.match(''.join(test_string.splitlines()))


# TODO: Maybe cleaner to make the split between strict/approximate
#       an argument instead of separate functions.


@lru_cache(maxsize=1024, typed=False)
def compare_text_approximate(x, y, maxlen=None):
    # Fast cutoff when one is empty
    if bool(x) != bool(y):
        return False

    if isinstance(x, list):
        x = "".join(x)
    if isinstance(y, list):
        y = "".join(y)

    # TODO: Review whether this is wanted.
    #       The motivation is to align tiny
    #       strings in outputs such as a single number.
    # Allow aligning short strings without comparison
    nx = len(x)
    ny = len(y)
    shortlen = 10  # TODO: Add this to configuration framework
    if nx < shortlen and ny < shortlen:
        return True

    return compare_strings_approximate(x, y, threshold=0.7, maxlen=maxlen)


def compare_text_strict(x, y, maxlen=None):
    # TODO: Doesn't have to be 100% equal here?
    if isinstance(x, list):
        x = "".join(x)
    if isinstance(y, list):
        y = "".join(y)
    if len(x) == len(y) and x == y:
        return True
    return compare_strings_approximate(x, y, threshold=0.95, maxlen=maxlen)


def make_compare_text(maxlen, strict):
    def compare_text(x, y):
        if strict:
            return compare_text_strict(x, y, maxlen=maxlen)
        return compare_text_approximate(x, y, maxlen=maxlen)
    return compare_text


def compare_base64_strict(x, y):
    if len(x) != len(y):
        return False
    # TODO: Handle base64 data another way?
    return x == y


@lru_cache(maxsize=128, typed=False)
def _compare_mimedata_strings(x, y, comp_text, comp_base64):
    # Most likely base64 encoded data
    if _is_base64(x):
        return comp_base64(x, y)
    else:
        return comp_text(x, y)


def _compare_mimedata(mimetype, x, y, comp_text, comp_base64):
    mimetype = mimetype.lower()

    # TODO: Test this. Match repr-style oneliners with random pointer
    if mimetype == "text/plain":
        # Allow short texts to only differ by pointer values
        if "\n" not in x and "\n" not in y:
            xsplit = re_pointer.split(x)
            ysplit = re_pointer.split(y)
            if xsplit == ysplit:
                return True

    if mimetype.startswith("text/"):
        return comp_text(x, y)

    # TODO: Compare binary images?
    #if mimetype.startswith("image/"):
    if isinstance(x, str) and isinstance(y, str):
        return _compare_mimedata_strings(x, y, comp_text, comp_base64)
    # Fallback to exactly equal
    return x == y


def compare_mimedata_approximate(mimetype, x, y):
    return _compare_mimedata(
        mimetype, x, y,
        make_compare_text(maxlen=TEXT_MIMEDATA_MAX_COMPARE_LENGTH, strict=False),
        compare_base64_strict)


def compare_mimedata_strict(mimetype, x, y):
    return _compare_mimedata(
        mimetype, x, y,
        make_compare_text(maxlen=TEXT_MIMEDATA_MAX_COMPARE_LENGTH, strict=True),
        compare_base64_strict)


def compare_mimebundle_approximate(x, y):
    # Get the simple and cheap stuff out of the way
    if x is None and y is None:
        return True
    if x is None or y is None:
        return False

    # This only checks that the same mime types are present
    if set(x.keys()) != set(y.keys()):
        return False

    for key in x.keys():
        # Delegate to mimetype specific comparison
        if not compare_mimedata_approximate(key, x[key], y[key]):
            return False

    # Didn't fail up to here it must be equal
    return True


def compare_mimebundle_strict(x, y):
    # Get the simple and cheap stuff out of the way
    if x is None and y is None:
        return True
    if x is None or y is None:
        return False

    # This only checks that the same mime types are present
    if set(x.keys()) != set(y.keys()):
        return False

    for key in x.keys():
        # Delegate to mimetype specific comparison
        if not compare_mimedata_strict(key, x[key], y[key]):
            return False

    # Didn't fail up to here it must be equal
    return True


def compare_tracebacks(xt, yt):
    if len(xt) != len(yt):
        return False
    for x, y in zip(xt, yt):
        if not compare_strings_approximate(x, y):
            return False
    return True


def compare_output_approximate(x, y):
    "Compare type and data of output cells x,y approximately."
    # NB! This is used as a basis by the exact compare_output.

    # Fast cutuff
    ot = x["output_type"]
    if ot != y["output_type"]:
        return False

    # Sanity cutoff
    xkeys = set(x)
    ykeys = set(y)
    if xkeys != ykeys:
        return False

    # Deliberately skipping metadata and execution count here
    handled = set(("output_type", "metadata", "execution_count"))

    if ot == "stream":
        if x["name"] != y["name"]:
            return False
        if not compare_strings_approximate(x["text"], y["text"], maxlen=STREAM_MAX_COMPARE_LENGTH):
            return False
        handled.update(("name", "text"))

    elif ot == "error":
        if x["ename"] != y["ename"]:
            return False
        if x["evalue"] != y["evalue"]:
            return False

        # Compare tracebacks
        xt = x["traceback"]
        yt = y["traceback"]
        if not compare_tracebacks(xt, yt):
            return False

        handled.update(("ename", "evalue", "traceback"))

    elif ot == "display_data" or ot == "execute_result":
        xd = x["data"]
        yd = y["data"]
        if not compare_mimebundle_approximate(xd, yd):
            return False
        handled.update(("data",))

    else:
        # Unknown type
        pass

    # Play safe on unknown keys
    for k in xkeys - handled:
        if x[k] != y[k]:
            return False

    # NB! Ignoring metadata and execution count
    return True


def compare_output_strict(x, y):
    "Compare type and data of output cells x,y to higher accuracy."

    # Fast cutuff
    ot = x["output_type"]
    if ot != y["output_type"]:
        return False

    # Sanity cutoff
    xkeys = set(x)
    ykeys = set(y)
    if xkeys != ykeys:
        return False

    handled = set(("output_type", "data"))

    # Strict match on all keys we do not otherwise handle
    for k in xkeys - handled:
        if x[k] != y[k]:
            return False

    if not compare_mimebundle_strict(x.get("data"), y.get("data")):
        return False

    # NB! Ignoring metadata and execution count
    return True


def compare_cell_approximate(x, y):
    """Compare cells x,y with approximate heuristics.

    This is used to align cells in the /cells list
    in the third and last multilevel diff iteration.
    """
    # Cell types must match
    if x["cell_type"] != y["cell_type"]:
        return False

    # Compare sources
    if not compare_text_approximate(x["source"], y["source"]):
        return False

    # NB! Ignoring metadata, execution_count, outputs
    return True


def compare_outputs_approximate(xoutputs, youtputs):
    """Compare sequences of outputs with approximate heuristics."""
    dd = diff_item_at_path(xoutputs, youtputs, "/cells/*/outputs")
    if any(e.op != DiffOp.PATCH for e in dd):
        # Something added or removed
        return False
    # If nothing was added or removed, that means all
    # items in outputs lists are determined to align
    return True


def compare_cell_moderate(x, y):
    """Compare cells x,y with moderate accuracy heuristics.

    This is used to align cells in the /cells list
    in the second multilevel diff iteration.
    """

    # Cell types must match
    if x["cell_type"] != y["cell_type"]:
        return False

    # Compare sources
    if not compare_text_approximate(x["source"], y["source"]):
        return False

    # Compare outputs for code cells
    if x["cell_type"] == "code":
        xop = x["outputs"] or ()
        yop = y["outputs"] or ()
        if bool(xop) != bool(yop):
            return False
        return compare_outputs_approximate(xop, yop)

    # NB! Ignoring metadata and execution_count
    return True


def compare_cell_strict(x, y):
    """Compare cells x,y with higher accuracy heuristics.

    This is used to align cells in the /cells list
    in the first multilevel diff iteration.
    """

    # Cell types must match
    if x["cell_type"] != y["cell_type"]:
        return False

    # Compare sources
    if not compare_text_strict(x["source"], y["source"]):
        return False

    # Compare outputs for code cells
    if x["cell_type"] == "code":
        xop = x["outputs"] or ()
        yop = y["outputs"] or ()
        # Be strict on number of outputs
        if len(xop) != len(yop):
            return False
        # Be strict on order and content of outputs
        for xo, yo in zip(xop, yop):
            if not compare_output_strict(xo, yo):
                return False

    # NB! Ignoring metadata and execution count
    return True


def compare_cell_by_ids(x, y):
    """Compare cells x,y strictly using cell IDs"""
    # Only consider equal if both have IDs and they match
    return 'id' in x and 'id' in y and x['id'] == y['id']


def diff_single_outputs(a, b, path="/cells/*/outputs/*", config=None):
    """DiffOp a pair of output cells."""
    assert path == "/cells/*/outputs/*", 'Invalid path for ouput: %r' % path
    assert a.output_type == b.output_type, 'cannot diff outputs of different types'

    if a.output_type in ("execute_result", "display_data"):
        di = MappingDiffBuilder()

        # Separate data from output during diffing:
        tmp_data = a.pop('data')
        a_conj = copy.deepcopy(a)  # Output without data
        a.data = tmp_data          # Restore output
        tmp_data = b.pop('data')
        b_conj = copy.deepcopy(b)
        b.data = tmp_data
        # Only diff outputs without data:
        dd_conj = diff(a_conj, b_conj)
        if dd_conj:
            for e in dd_conj:
                di.append(e)

        # Only diff data:
        dd = diff_mime_bundle(a.data, b.data, path=path+"/data", config=config)
        if dd:
            di.patch("data", dd)

        return di.validated()
    else:
        return diff(a, b, config=config)


def add_mime_diff(key, avalue, bvalue, diffbuilder):
    # TODO: Handle output diffing with plugins?
    # I.e. image diff, svg diff, json diff, etc.

    mimetype = key.lower()
    if isinstance(avalue, str) and isinstance(bvalue, str) and avalue == bvalue:
        return
    if any(mimetype.startswith(tm) for tm in _split_mimes):
        dd = diff(avalue, bvalue)
        if dd:
            diffbuilder.patch(key, dd)
    elif avalue != bvalue:
        diffbuilder.replace(key, bvalue)


def diff_attachments(a, b, path="/cells/*/attachments", config=None):
    """Diff a pair of attachment collections"""
    assert path == "/cells/*/attachments", 'Invalid path for attachment: %r' % path

    # Two events can happen:
    #  1: An attachment is added/removed/patched
    #  2: An attachment is renamed (key change)
    # Currently, #2 is handled as two ops (an add and a remove)

    # keys here are 'filenames' of the attachments
    if not isinstance(a, dict) or not isinstance(b, dict):
        raise TypeError('Attachments stores should be dictionaries. Got %r and %r' % (a, b))
    akeys = set(a.keys())
    bkeys = set(b.keys())

    di = MappingDiffBuilder()

    # Sorting keys in loops to get a deterministic diff result
    for key in sorted(akeys - bkeys):
        di.remove(key)

    # Handle values for keys in both a and b
    for key in sorted(akeys & bkeys):
        avalue = a[key]
        bvalue = b[key]

        dd = diff_mime_bundle(avalue, bvalue)
        if dd:
            di.patch(key, dd)

    for key in sorted(bkeys - akeys):
        di.add(key, b[key])
    return di.validated()


def diff_mime_bundle(a, b, path=None, config=None):
    """Diff a MIME bundle.

    A MIME bundle has MIME types as keys, with values that are
    of the corresponding MIME type.

    Very similar to the generic dict differ, except it passes
    the diff builder to the sub-differ.
    """
    # keys here are mime/types
    if not isinstance(a, dict) or not isinstance(b, dict):
        raise TypeError('MIME bundles should be dictionaries. Got %r and %r' % (a, b))
    akeys = set(a.keys())
    bkeys = set(b.keys())

    di = MappingDiffBuilder()

    # Sorting keys in loops to get a deterministic diff result
    for key in sorted(akeys - bkeys):
        di.remove(key)

    # Handle values for keys in both a and b
    for key in sorted(akeys & bkeys):
        avalue = a[key]
        bvalue = b[key]
        add_mime_diff(key, avalue, bvalue, di)

    for key in sorted(bkeys - akeys):
        di.add(key, b[key])
    return di.validated()


def diff_ignore(*args, **kwargs):
    """Always returns an empty diff"""
    return []


def diff_ignore_keys(inner_differ, ignore_keys):
    """Call inner_differ, but filter the resulting diff.

    Will ignore all direct diff values that has a key in
    ignore_keys. I.e. this will not recurse into patch ops.
    """
    def ignored_diff(*args, **kwargs):
        d = inner_differ(*args, **kwargs)
        ret = []
        for e in d:
            if e.key not in ignore_keys:
                ret.append(e)
        return ret
    return ignored_diff


# Sequence diffs should be applied with multilevel
# algorithm for paths with more than one predicate,
# and using operator.__eq__ if no match in there.
notebook_predicates = defaultdict2(lambda: [operator.__eq__], {
    # Predicates to compare cells in order of low-to-high precedence
    "/cells": [
        compare_cell_approximate,
        compare_cell_moderate,
        compare_cell_strict,
        compare_cell_by_ids,
        ],
    # Predicates to compare output cells (within one cell) in order of low-to-high precedence
    "/cells/*/outputs": [
        compare_output_approximate,
        compare_output_strict,
        ]
    })

# Recursive diffing of substructures should pick a rule from here, with diff as fallback
notebook_differs = defaultdict2(lambda: diff, {
    "/cells": diff_sequence_multilevel,
    "/cells/*": diff,
    "/cells/*/source": diff_string_lines,
    "/cells/*/outputs": diff_sequence_multilevel,
    "/cells/*/outputs/*": diff_single_outputs,
    "/cells/*/attachments": diff_attachments,
    })


notebook_config = DiffConfig(
    predicates=notebook_predicates,
    differs=notebook_differs,
    atomic_paths={
        "/cells/*/id": True
    }
)


def reset_notebook_differ():
    """Reset the notebook_differs dictionary to default values."""
    # As it is a defaultdict2, simply clear all set keys to reset:
    for key in tuple(notebook_differs.keys()):
        del notebook_differs[key]


def set_notebook_diff_ignores(ignore_paths):
    """Set/unset notebook differs to ignore.

    Parameters:
        ignore_paths: dict
            Dictionary with path strings (e.g. /cells/*/outputs) as keys.
            For each entry in the dictionary do the following:
            - if value is True, set path to `diff_ignore`.
            - if value is False, reset the differ of path to the default value.
            - if value is set/tuple/list, assume the container is a collection
              of subkeys of path to ignore with `diff_ignore_keys`.
    """
    for path, subkeys in ignore_paths.items():
        if subkeys is True:
            notebook_differs[path] = diff_ignore
        elif subkeys is False:
            if path in notebook_differs:
                del notebook_differs[path]
        elif isinstance(subkeys, (list, tuple, set)):
            notebook_differs[path] = diff_ignore_keys(notebook_differs[path], subkeys)
        else:
            raise ValueError('Invalid ignore config entry: %r: %r' % (path, subkeys))


def set_notebook_diff_targets(sources=True, outputs=True, attachments=True,
                              metadata=True, identifier=True, details=True):
    """Configure the notebook differs to include/ignore various changes."""

    config = {
        '/cells/*/source': not sources,
        '/cells/*/outputs': not outputs,
        '/cells/*/attachments': not attachments,
        '/metadata': not metadata,
        '/cells/*/id': not identifier,
        '/cells/*/metadata': not metadata,
        '/cells/*/outputs/*/metadata': not metadata,
        '/cells/*': False if details else ('execution_count',),
        '/cells/*/outputs/*': False if details else ('execution_count',),
    }
    set_notebook_diff_ignores(config)


def diff_cells(a, b):
    "This is currently just used by some tests."
    path = "/cells"
    return notebook_differs[path](a, b, path=path, config=notebook_config)


def diff_item_at_path(a, b, path):
    """Calculate the diff using the configured notebook differ for path."""
    return notebook_differs[path](a, b, path=path, config=notebook_config)


def diff_notebooks(a, b):
    """Compute the diff of two notebooks using customized heuristics and diff rules.

    The notebooks are expected in the format of nbformat's version 4.
    """
    if not (isinstance(a, dict) and isinstance(b, dict)):
        raise TypeError("Expected inputs to be dicts, got %r and %r" % (a, b))
    return diff(a, b, path="", config=notebook_config)
