# coding: utf-8

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import unicode_literals
from __future__ import print_function

from itertools import chain
import sys
import io
import os
import time
import datetime
import pprint
import re
import shutil
from subprocess import Popen, PIPE
import tempfile
from difflib import unified_diff
from six import string_types
import hashlib
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
from .utils import star_path, split_path, join_path


# Change to enable/disable color print etc.
_git_diff_print_cmd = 'git diff --no-index --color-words'

# colors
REMOVE = colorama.Fore.RED + '-  '
ADD = colorama.Fore.GREEN + '+  '
RESET = colorama.Style.RESET_ALL

# indentation offset
IND = "  "


_base64 = re.compile(r'^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$', re.MULTILINE|re.UNICODE)

def _trim_base64(s):
    """Trim base64 strings"""
    if len(s) > 64 and _base64.match(s.replace('\n', '')):
        h = hashlib.md5(s).hexdigest()
        s = '%s...<snip base64 with md5=%s>...%s' % (s[:16], h, s[-16:].strip())
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


def pretty_print_changed_value(arg, path, prefix="", out=sys.stdout):
    """Present a whole value that is either added or deleted.

    Calls out to other formatters for cells, outputs, and multiline strings.

    Uses pprint.pformat, otherwise.
    """
    # Format starred version of path
    if path is None:
        starred = None
    else:
        if path.startswith('/'):
            path_prefix, path_trail = ('', path)
        else:
            path_prefix, path_trail = path.split('/', 1)
        starred = star_path(split_path(path_trail))

    # Check if we can handle path with specific formatter
    if starred is not None:
        if starred == "/cells/*":
            for cell in arg:
                pretty_print_cell(None, cell, prefix, out)
        elif starred == "/cells":
            pretty_print_cell(None, arg, prefix, out)
        elif starred == "/cells/*/outputs/*":
            for output in arg:
                pretty_print_output(None, output, prefix, out)
        elif starred == "/cells/*/outputs":
            pretty_print_output(None, arg, prefix, out)
        elif starred == "/cells/*/attachments":
            pretty_print_attachments(arg, prefix, out)
        else:
            starred = None

    # No path or path not handled
    if starred is None:
        if isinstance(arg, string_types):
            pretty_print_multiline(arg, prefix, out)
        elif isinstance(arg, dict):
            pretty_print_dict(arg, (), prefix, out)
        elif isinstance(arg, list) and arg:
            pretty_print_list(arg, prefix, out)
            #for i, element in enumerate(arg):
            #    nextpath = "/".join((path, str(i)))
            #    pretty_print_changed_value(element, nextpath, prefix+IND, out)
        else:
            pretty_print_multiline(pprint.pformat(arg), prefix, out)


def pretty_print_diff_entry(a, e, path, out=sys.stdout):
    key = e.key
    nextpath = "/".join((path, str(key)))
    op = e.op

    # Recurse to handle patch ops
    if op == DiffOp.PATCH:
        # NB! Not indenting further here, allowing path to contain debth information
        pretty_print_diff(a[key], e.diff, nextpath, out)
        return

    if op == DiffOp.ADDRANGE:
        out.write("insert before {}:\n".format(nextpath))
        pretty_print_changed_value(e.valuelist, nextpath, ADD, out)

    elif op == DiffOp.REMOVERANGE:
        if e.length > 1:
            keyrange = "{}-{}".format(nextpath, key + e.length - 1)
        else:
            keyrange = nextpath
        out.write("delete {}:\n".format(nextpath))
        pretty_print_changed_value(a[key: key + e.length], nextpath, REMOVE, out)

    elif op == DiffOp.REMOVE:
        out.write("delete {}:\n".format(nextpath))
        pretty_print_changed_value(a[key], nextpath, REMOVE, out)

    elif op == DiffOp.ADD:
        out.write("insert {}:\n".format(nextpath))
        pretty_print_changed_value(e.value, nextpath, ADD, out)

    elif op == DiffOp.REPLACE:
        out.write("replace {}:\n".format(nextpath))
        pretty_print_changed_value(a[key], nextpath, REMOVE, out)
        pretty_print_changed_value(e.value, nextpath, ADD, out)

    else:
        raise NBDiffFormatError("Unknown list diff op {}".format(op))

    out.write(RESET)
    #out.write("\n")


def pretty_print_dict_diff(a, di, path, out=sys.stdout):
    "Pretty-print a nbdime diff."
    for key, e in sorted((e.key, e) for e in di):
        pretty_print_diff_entry(a, e, path, out)


def pretty_print_list_diff(a, di, path, out=sys.stdout):
    "Pretty-print a nbdime diff."
    for e in di:
        pretty_print_diff_entry(a, e, path, out)


def pretty_print_string_diff(a, di, path, out=sys.stdout):
    "Pretty-print a nbdime diff."
    b = patch(a, di)

    if _base64.match(a):
        ah = hashlib.md5(a).hexdigest()
        bh = hashlib.md5(b).hexdigest()
        out.write('%s<base64 data with md5=%s>\n' % (REMOVE, ah))
        out.write('%s<base64 data with md5=%s>\n' % (ADD, bh))
        return

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


def pretty_print_diff(a, di, path, out=sys.stdout):
    "Pretty-print a nbdime diff."
    if isinstance(a, dict):
        pretty_print_dict_diff(a, di, path, out)
    elif isinstance(a, list):
        pretty_print_list_diff(a, di, path, out)
    elif isinstance(a, string_types):
        pretty_print_string_diff(a, di, path, out)
    else:
        raise NBDiffFormatError("Invalid type {} for diff presentation.".format(type(a)))


notebook_diff_header = """\
nbdiff {afn} {bfn}
--- a: {afn}{atime}
+++ b: {bfn}{btime}
"""


def file_timestamp(filename):
    st = os.stat(filename)
    lt = time.localtime(st.st_mtime)
    t = datetime.time(lt.tm_hour, lt.tm_min, lt.tm_sec)
    d = datetime.date(lt.tm_year, lt.tm_mon, lt.tm_mday)
    return "%s %s" % (d.isoformat(), t.isoformat())


def pretty_print_notebook_diff(afn, bfn, a, di, out=sys.stdout):
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
        try:
            atime = "  " + file_timestamp(afn)
            btime = "  " + file_timestamp(bfn)
        except:
            atime = ""
            btime = ""
        out.write(notebook_diff_header.format(afn=afn, bfn=bfn, atime=atime, btime=btime))
        pretty_print_diff(a, di, path, out)


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
            pretty_print_item(k, v, prefix, out)


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


def pretty_print_attachments(attachments, prefix="", out=sys.stdout):
    out.write("%s%s:\n" % (prefix, "attachments"))
    for name in sorted(attachments):
        out.write("%s%s:\n" % (prefix+IND, name))
        pretty_print_dict(attachments[name], (), prefix+IND*2, out)


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
    attachments = cell.get("attachments")
    if attachments:
        pretty_print_attachments(attachments, key_prefix, out)

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
