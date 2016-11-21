# coding: utf-8

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import unicode_literals
from __future__ import print_function

from itertools import chain
import sys
import io
import os
import pprint
import re
import shutil
from subprocess import Popen, PIPE
import tempfile
from difflib import unified_diff
from six import string_types
import colorama

try:
    from textwrap import indent
except ImportError:
    def indent(text, prefix):
        """The relevant part of textwrap.indent for Python 2"""
        return prefix + text.replace('\n', '\n' + prefix)

try:
    from shutil import which
except ImportError:
    from backports.shutil_which import which

from .diff_format import NBDiffFormatError, DiffOp
from .patching import patch


# Toggle indentation here
with_indent = False

# Change to enable/disable color print etc.
_git_diff_print_cmd = 'git diff --no-index --color-words'

# colors
REMOVE = colorama.Fore.RED + '-'
ADD = colorama.Fore.GREEN + '+'
RESET = colorama.Style.RESET_ALL

# indentation offset
IND = "  "


_base64 = re.compile(r'^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$', re.MULTILINE|re.UNICODE)

def _trim_base64(s):
    """Trim base64 strings"""
    if len(s) > 64 and _base64.match(s.replace('\n', '')):
        s = s[:16] + '...<snip base64>...' + s[-16:].strip()
    return s


def _external_diff_render(cmd, a, b):
    try:
        td = tempfile.mkdtemp()
        with io.open(os.path.join(td, 'before'), 'w', encoding="utf8") as f:
            f.write(a)
        with io.open(os.path.join(td, 'after'), 'w', encoding="utf8") as f:
            f.write(b)
        p = Popen(cmd + ['before', 'after'], cwd=td, stdout=PIPE)
        out, _ = p.communicate()
        diff = out.decode('utf8')
    finally:
        shutil.rmtree(td)
    return diff


def _builtin_diff_render(a, b):
    gen = unified_diff(
        a.splitlines(False),
        b.splitlines(False),
        lineterm='')
    uni = []
    for line in gen:
        if line.startswith('+'):
            uni.append("%s%s%s" % (ADD, line[1:], RESET))
        elif line.startswith('-'):
            uni.append("%s%s%s" % (REMOVE, line[1:], RESET))
        else:
            uni.append(line)
    if not a.endswith('\n'):
        uni.insert(-1, r'\ No newline at end of file')
    if not b.endswith('\n'):
        uni.append(r'\ No newline at end of file')
    diff = '\n'.join(uni)
    return diff


def pretty_print_changed_value(arg, prefix="", out=sys.stdout):
    """Present a whole value that is either added or deleted.

    Calls out to other formatters for cells, outputs, and multiline strings.

    Uses pprint.pformat, otherwise.
    """
    # TODO: Improve pretty-print of arbitrary values?
    # TODO: Use paths to map to other cases than cells and outputs?

    if isinstance(arg, dict):
        if 'cell_type' in arg:
            pretty_print_cell(None, arg, prefix, out)
        elif 'output_type' in arg:
            pretty_print_output(None, arg, prefix, out)
        else:
            pretty_print_dict(arg, (), prefix, out)
    elif isinstance(arg, list) and arg:
        for element in arg:
            pretty_print_changed_value(element, prefix+IND, out)
    elif isinstance(arg, string_types):
        pretty_print_multiline(arg, prefix, out)
    else:
        lines = pprint.pformat(arg).splitlines()
        for line in lines:
            out.write(prefix + line + "\n")


def pretty_print_diff_entry(a, e, path, prefix="", out=sys.stdout):
    # NB! Ignoring prefix below, setting to ADD, REMOVE etc. instead.

    key = e.key
    nextpath = "/".join((path, str(key)))
    op = e.op

    # Recurse to handle patch ops
    if op == DiffOp.PATCH:
        # NB! Not indenting further here, allowing path to contain debth information
        pretty_print_diff(a[key], e.diff, nextpath, prefix, out)
        return

    if op == DiffOp.ADDRANGE:
        out.write("insert before {}:\n".format(nextpath))
        pretty_print_changed_value(e.valuelist, ADD, out)

    elif op == DiffOp.REMOVERANGE:
        if e.length > 1:
            r = "{}-{}".format(key, key + e.length - 1)
        else:
            r = str(key)
        out.write("delete {}/{}:\n".format(path, r))
        pretty_print_changed_value(a[key: key + e.length], REMOVE, out)

    elif op == DiffOp.REMOVE:
        out.write("delete from {}:\n".format(nextpath))
        pretty_print_changed_value(a[key], REMOVE, out)

    elif op == DiffOp.ADD:
        out.write("insert at {}:\n".format(nextpath))
        pretty_print_changed_value(e.value, ADD, out)

    elif op == DiffOp.REPLACE:
        out.write("replace at {}:\n".format(nextpath))
        pretty_print_changed_value(a[key], REMOVE, out)
        pretty_print_changed_value(e.value, ADD, out)

    else:
        raise NBDiffFormatError("Unknown list diff op {}".format(op))

    out.write(RESET)
    out.write("\n")


def pretty_print_dict_diff(a, di, path, prefix="", out=sys.stdout):
    "Pretty-print a nbdime diff."
    for key, e in sorted((e.key, e) for e in di):
        pretty_print_diff_entry(a, e, path, prefix, out)


def pretty_print_list_diff(a, di, path, prefix="", out=sys.stdout):
    "Pretty-print a nbdime diff."
    for e in di:
        pretty_print_diff_entry(a, e, path, prefix, out)


def pretty_print_string_diff(a, di, path, prefix="", out=sys.stdout):
    "Pretty-print a nbdime diff."
    if _base64.match(a):
        out.write(prefix + '<base64 data changed>\n')
        return

    b = patch(a, di)

    if which('git'):
        diff = _external_diff_render(_git_diff_print_cmd.split(), a, b)
        heading_lines = 4
    elif which('diff'):
        diff = _external_diff_render(['diff'], a, b)
        heading_lines = 0
    else:
        diff = _builtin_diff_render(a, b)
        heading_lines = 2

    # NB! Ignoring prefix here!
    diff_lines = diff.splitlines()[heading_lines:]
    out.write("\n".join(diff_lines))


def pretty_print_diff(a, di, path, prefix="", out=sys.stdout):
    "Pretty-print a nbdime diff."
    if isinstance(a, dict):
        pretty_print_dict_diff(a, di, path, prefix, out)
    elif isinstance(a, list):
        pretty_print_list_diff(a, di, path, prefix, out)
    elif isinstance(a, string_types):
        pretty_print_string_diff(a, di, path, prefix, out)
    else:
        raise NBDiffFormatError("Invalid type {} for diff presentation.".format(type(a)))


notebook_diff_header = """\
nbdiff {afn} {bfn}
--- a: {afn}
+++ b: {bfn}
"""


def pretty_print_notebook_diff(afn, bfn, a, di, prefix="", out=sys.stdout):
    """Pretty-print a notebook diff

    Parameters
    ----------

    afn: str
        Filename of a, the base notebook
    bfn: str
        Filename of b, the updated notebook
    a: dict
        The base notebook object
    di: diff
        The diff object describing the transformation from a to b
    """
    if di:
        path = ""
        out.write(notebook_diff_header.format(afn=afn, bfn=bfn))
        pretty_print_diff(a, di, path, prefix, out)


def pretty_print_merge_decision(decision, prefix="", out=sys.stdout):
    pretty_print_dict(decision, prefix, out)


def pretty_print_merge_decisions(base, decisions, prefix="", out=sys.stdout):
    """Pretty-print notebook merge decisions

    Parameters
    ----------

    base: dict
        The base notebook object
    decisions: list
        The list of merge decisions
    """
    conflicted = [d for d in decisions if d.conflict]
    out.write("%s%d conflicted decisions of %d total:\n"
              % (prefix, len(conflicted), len(decisions)))
    for d in decisions:
        pretty_print_merge_decision(d, prefix+IND, out)
        out.write("\n")
    out.write("\n")


def pretty_print_notebook_merge(bfn, lfn, rfn, bnb, lnb, rnb, mnb, decisions, out=sys.stdout):
    """Pretty-print a notebook diff

    Parameters
    ----------

    bfn: str
        Filename of the base notebook
    lfn: str
        Filename of the local notebook
    rfn: str
        Filename of the remote notebook
    bnb: dict
        The base notebook object
    lnb: dict
        The local notebook object
    rnb: dict
        The remote notebook object
    mnb: dict
        The partially merged notebook object
    decisions: list
        The list of merge decisions including conflicts
    """
    pretty_print_merge_decisions(bnb, decisions, "", out)


def pretty_print_item(k, v, prefix="", out=sys.stdout):
    if isinstance(v, string_types):
        vstr = v
        if "\n" in vstr:
            # Multiline strings
            out.write("%s%s:\n" % (prefix, k))
            for line in vstr.splitlines(False):
                out.write("%s'%s\n'\n" % (prefix+IND, line))
        else:
            # Singleline strings
            out.write("%s%s: %s\n" % (prefix, k, vstr))
    else:
        # Something else, cut large metadata values short
        vstr = repr(v)
        if len(vstr) > 60:
            vstr = "<%s instance: %s...>" % (v.__class__.__name__, vstr[:20])
        out.write("%s%s: %s\n" % (prefix, k, vstr))


def pretty_print_list(li, prefix="", out=sys.stdout):
    for k, v in enumerate(li):
        if isinstance(v, dict):
            # Nested dicts
            out.write("%s%s:\n" % (prefix, k))
            pretty_print_dict(v, (), prefix+IND, out)
        elif isinstance(v, list):
            # Nested lists
            out.write("%s%s:\n" % (prefix, k))
            pretty_print_list(v, prefix+IND, out)
        else:
            pretty_print_item(k, v, prefix+IND, out)


def pretty_print_dict(d, exclude_keys=(), prefix="", out=sys.stdout):
    """Pretty-print a dict without wrapper keys

    Instead of {'key': 'value'}, do

        key: value
        key:
          long
          value

    """
    for k in sorted(d):
        if k in exclude_keys:
            continue
        v = d[k]
        if isinstance(v, dict):
            # Nested dicts
            out.write("%s%s:\n" % (prefix, k))
            pretty_print_dict(v, (), prefix+IND, out)
        elif isinstance(v, list):
            # Nested lists
            out.write("%s%s:\n" % (prefix, k))
            pretty_print_list(v, prefix+IND, out)
        else:
            pretty_print_item(k, v, prefix+IND, out)


def pretty_print_metadata(md, known_keys, prefix="", out=sys.stdout):
    md1 = {}
    md2 = {}
    for k in md:
        if k in known_keys:
            md1[k] = md[k]
        else:
            md2[k] = md[k]
    if md1:
        out.write("%smetadata (known keys):\n" % (prefix,))
        pretty_print_dict(md1, (), prefix+IND, out)
    if md2:
        out.write("%smetadata (unknown keys):\n" % (prefix,))
        pretty_print_dict(md2, (), prefix+IND, out)


def pretty_print_multiline(text, prefix="", out=sys.stdout):
    assert isinstance(text, string_types)

    # Trim base64 strings (images etc)
    text = _trim_base64(text)

    # Preprend prefix to lines, letting lines keep their own newlines
    lines = text.splitlines(True)
    for line in lines:
        out.write(prefix + line)

    # If the final line doesn't have a newline,
    # make sure we still start a new line
    if not text.endswith("\n"):
        out.write("\n")


def pretty_print_output(i, output, prefix="", out=sys.stdout):
    oprefix = prefix+IND
    t = output.output_type
    numstr = "" if i is None else " %d" % i
    out.write("%s%s output%s:\n" % (prefix, t, numstr))

    metadata = output.get("metadata")
    if metadata:
        known_output_metadata_keys = {"isolated"}
        pretty_print_metadata(metadata, known_output_metadata_keys, oprefix, out)

    exclude_keys = {"output_type", "metadata", "execution_count", "name", "text", "data"}

    execution_count = output.get("execution_count")
    if execution_count:
        out.write("%sexecution_count: %s\n" % (oprefix, execution_count))

    name = output.get("name")
    if name:
        out.write("%sname: %s\n" % (oprefix, name))

    text = output.get("text")
    if text:
        out.write("%stext:\n" % (oprefix,))
        pretty_print_multiline(text, oprefix+IND, out)

    data = output.get("data")
    if data:
        out.write("%sdata:\n" % (oprefix,))
        pretty_print_dict(data, (), oprefix+IND, out)

    if t == "error":
        exclude_keys.update(("ename", "evalue", "traceback"))
        out.write("%sename: %s\n" % (oprefix, output.ename))
        out.write("%sevalue: %s\n" % (oprefix, output.evalue))
        out.write("%straceback:\n" % (oprefix,))
        pretty_print_list(output.traceback, oprefix+IND, out)

    pretty_print_dict(output, exclude_keys, oprefix, out)


def pretty_print_outputs(outputs, prefix="", out=sys.stdout):
    out.write("%soutputs:\n" % (prefix,))
    for i, output in enumerate(outputs):
        pretty_print_output(i, output, prefix+IND, out)


def pretty_print_attachment(attachment, prefix="", out=sys.stdout):
    out.write("%sattachment:\n" % (prefix,))
    pretty_print_dict(attachment, (), prefix+IND, out)


def pretty_print_source(source, prefix="", out=sys.stdout):
    out.write("%ssource:\n" % (prefix,))
    pretty_print_multiline(source, prefix+IND, out)


def pretty_print_cell(i, cell, prefix="", out=sys.stdout):
    # Write cell type and optionally number:
    numstr = "" if i is None else " %d" % i
    out.write("%s%s cell%s:\n" % (prefix, cell.cell_type, numstr))

    key_prefix = prefix+IND

    # Write execution count if there (only source cells)
    if "execution_count" in cell:
        out.write("%sexecution_count: %s\n" % (key_prefix, repr(cell.execution_count)))

    # Write cell metadata
    known_cell_metadata_keys = {"collapsed", "autoscroll", "deletable", "format", "name", "tags"}
    pretty_print_metadata(cell.metadata, key_prefix, out)

    # Write source
    source = cell.get("source")
    if source:
        pretty_print_source(source, key_prefix, out)

    # Write outputs if there (only source cells)
    outputs = cell.get("outputs")
    if outputs:
        pretty_print_outputs(outputs, key_prefix, out)

    # Write attachment if there (only markdown and raw cells)
    attachment = cell.get("attachment")
    if attachment:
        pretty_print_attachment(attachment, key_prefix, out)

    # present_value on anything we haven't special-cased yet
    exclude_keys = {'cell_type', 'source', 'execution_count', 'outputs', 'metadata', 'attachment'}
    pretty_print_dict(cell, exclude_keys, key_prefix, out)


def pretty_print_notebook(nb, out=sys.stdout):
    """Pretty-print a notebook for debugging, skipping large details in metadata and output

    Parameters
    ----------

    nb: dict
        The notebook object
    out: file-like object
        File-like object with .write function used for output.
    """

    # Write notebook header
    out.write("notebook format: %d.%d\n" % (nb.nbformat, nb.nbformat_minor))

    # Report unknown keys
    unknown_keys = set(nb.keys()) - {"nbformat", "nbformat_minor", "metadata", "cells"}
    if unknown_keys:
        out.write("unknown keys: %r" % (unknown_keys,))

    # Write notebook metadata
    known_metadata_keys = {"kernelspec"}
    pretty_print_metadata(nb.metadata, known_metadata_keys, "", out)

    # Write notebook cells
    for i, cell in enumerate(nb.cells):
        pretty_print_cell(i, cell, "", out)
