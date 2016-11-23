# -*- coding: utf-8 -*-

# Copyright (c) Jupyter Development Team.
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

#try:
#    from textwrap import indent
#except ImportError:
#    def indent(text, prefix):
#        """The relevant part of textwrap.indent for Python 2"""
#        return prefix + text.replace('\n', '\n' + prefix)

try:
    from shutil import which
except ImportError:
    from backports.shutil_which import which

from .diff_format import NBDiffFormatError, DiffOp
from .patching import patch
from .utils import star_path, split_path, join_path

# TODO: Make this configurable
use_git = True
use_diff = True
use_colors = True

# Indentation offset in pretty-print
IND = "  "

# Max line width used some placed in pretty-print
# TODO: Use this for line wrapping some places?
MAXWIDTH = 78

if use_colors:
    import colorama
    RED = colorama.Fore.RED
    GREEN = colorama.Fore.GREEN
    BLUE = colorama.Fore.BLUE
    RESET = colorama.Style.RESET_ALL
    _git_diff_print_cmd = 'git diff --no-index --color-words'
else:
    RED = ''
    GREEN = ''
    BLUE = ''
    RESET = ''
    _git_diff_print_cmd = 'git diff --no-index'

REMOVE   = '{color}-  '.format(color=RED)
ADD      = '{color}+  '.format(color=GREEN)
INFO     = '{color}## '.format(color=BLUE)
DIFF_ENTRY_END = '\n'

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

def _diff_render_with_git(a, b):
    diff = _external_diff_render(_git_diff_print_cmd.split(), a, b)
    return diff.splitlines()[4:]


def _diff_render_with_diff(a, b):
    diff = _external_diff_render(['diff'], a, b)
    return diff.splitlines()


def _diff_render_with_difflib(a, b):
    diff = _builtin_diff_render(a, b)
    return diff.splitlines()[2:]


def _diff_render(a, b):
    if use_git and which('git'):
        return _diff_render_with_git(a, b)
    elif use_diff and which('diff'):
        return _diff_render_with_diff(a, b)
    else:
        return _diff_render_with_difflib(a, b)


_base64 = re.compile(r'^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$', re.MULTILINE|re.UNICODE)

def _trim_base64(s):
    """Trim base64 strings"""
    if len(s) > 64 and _base64.match(s.replace('\n', '')):
        h = hashlib.md5(s).hexdigest()
        #s = '%s...<snip base64 with md5=%s>...%s' % (s[:16], h, s[-16:].strip())
        s =  '%s...<snip base64, md5=%s...>' % (s[:8], h[:16])
    return s

def pretty_print_value(arg, path, prefix="", out=sys.stdout):
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
        if isinstance(arg, dict):
            pretty_print_dict(arg, (), prefix, out)
        elif isinstance(arg, list) and arg:
            pretty_print_list(arg, prefix, out)  # TODO: Pass path_trail here to allow formatting as listname[k]:? 
        else:
            pretty_print_multiline(format_value(arg), prefix, out)


def pretty_print_diff_entry(a, e, path, out=sys.stdout):
    key = e.key
    nextpath = "/".join((path, str(key)))
    op = e.op

    # Recurse to handle patch ops
    if op == DiffOp.PATCH:
        # Useful for debugging:
        #if not (len(e.diff) == 1 and e.diff[0].op == DiffOp.PATCH):
        #    out.write("{}// patch -+{} //{}\n".format(INFO, nextpath, RESET))
        #else:
        #    out.write("{}// patch... -+{} //{}\n".format(INFO, nextpath, RESET))
        pretty_print_diff(a[key], e.diff, nextpath, out)
        return

    if op == DiffOp.ADDRANGE:
        out.write("{}inserted before {}:{}\n".format(INFO, nextpath, RESET))
        pretty_print_value(e.valuelist, nextpath, ADD, out)

    elif op == DiffOp.REMOVERANGE:
        if e.length > 1:
            keyrange = "{}-{}".format(nextpath, key + e.length - 1)
        else:
            keyrange = nextpath
        out.write("{}deleted {}:{}\n".format(INFO, keyrange, RESET))
        pretty_print_value(a[key: key + e.length], nextpath, REMOVE, out)

    elif op == DiffOp.REMOVE:
        out.write("{}deleted {}:{}\n".format(INFO, nextpath, RESET))
        pretty_print_value(a[key], nextpath, REMOVE, out)

    elif op == DiffOp.ADD:
        out.write("{}added {}:{}\n".format(INFO, nextpath, RESET))
        pretty_print_value(e.value, nextpath, ADD, out)

    elif op == DiffOp.REPLACE:
        out.write("{}replaced {}:{}\n".format(INFO, nextpath, RESET))
        #aval = a[key]
        #bval = e.value
        # TODO: quote?
        pretty_print_value(a[key], nextpath, REMOVE, out)
        pretty_print_value(e.value, nextpath, ADD, out)

    else:
        raise NBDiffFormatError("Unknown list diff op {}".format(op))

    out.write(DIFF_ENTRY_END + RESET)


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
    out.write("{}modified {}:{}\n".format(INFO, path, RESET))

    #import pdb; pdb.set_trace()
    b = patch(a, di)  # FIXME: This fails in cli test, reproduce with py.test -k cli

    ta = _trim_base64(a)
    tb = _trim_base64(b)

    if ta != a or tb != b:
        if ta != a:
            out.write('%s%s\n' % (REMOVE, ta))
        else:
            pretty_print_value(a, path, REMOVE, out)
        if tb != b:
            out.write('%s%s\n' % (ADD, tb))
        else:
            pretty_print_value(b, path, ADD, out)
    elif "\n" in a or "\n" in b:
        # Delegate multiline diff formatting
        diff_lines = _diff_render(a, b)
        out.write("\n".join(diff_lines))
        out.write("\n")
    else:
        # Just show simple -+ single line (usually metadata values etc)
        out.write("%s%s\n" % (REMOVE, a))
        out.write("%s%s\n" % (ADD, b))

    out.write(DIFF_ENTRY_END + RESET)


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
--- {afn}{atime}
+++ {bfn}{btime}
"""

def file_timestamp(filename):
    t = os.path.getmtime(filename)
    dt = datetime.datetime.fromtimestamp(t)
    return dt.isoformat(b" ")


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
        #try:
        atime = "  " + file_timestamp(afn)
        btime = "  " + file_timestamp(bfn)
        #except:
        #    atime = ""
        #    btime = ""
        out.write(notebook_diff_header.format(afn=afn, bfn=bfn, atime=atime, btime=btime))
        pretty_print_diff(a, di, path, out)


def pretty_print_merge_decision(base, decision, out=sys.stdout):
    prefix = IND
    diff_keys = ["diff", "local_diff", "remote_diff", "custom_diff"]
    path = join_path(decision.common_path)
    out.write("%s====== decision at %s:%s\n" % (INFO, path, RESET))
    exclude_keys = set(diff_keys) | {"common_path"}
    pretty_print_dict(decision, exclude_keys, prefix, out)
    for dkey in diff_keys:
        diff = decision.get(dkey)
        if diff:
            out.write("%s=== %s:%s\n" % (INFO, dkey, RESET))
            value = base
            for k in decision.common_path:
                #diff.op
                if isinstance(value, string_types):
                    value = value.splitlines(True)[k]
                    break
                else:
                    value = value[k]
            pretty_print_diff(value, diff, path, out)


def pretty_print_merge_decisions(base, decisions, out=sys.stdout):
    """Pretty-print notebook merge decisions

    Parameters
    ----------

    base: dict
        The base notebook object
    decisions: list
        The list of merge decisions
    """
    conflicted = [d for d in decisions if d.conflict]
    out.write("%d conflicted decisions of %d total:\n"
              % (len(conflicted), len(decisions)))
    for d in decisions:
        pretty_print_merge_decision(base, d, out)
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
    pretty_print_merge_decisions(bnb, decisions, out)


def format_value(v):
    if not isinstance(v, string_types):
        # Not a string, defer to pprint
        vstr = pprint.pformat(v)
        # TODO: Cut strings short?
        #if len(vstr) > 60:
        #    vstr = "<%s instance: %s...>" % (v.__class__.__name__, vstr[:20])
    else:
        # Snip if base64 data
        vstr = _trim_base64(v)
    return vstr


def pretty_print_item(k, v, prefix="", out=sys.stdout):
    if isinstance(v, dict):
        out.write("%s%s:\n" % (prefix, k))
        pretty_print_dict(v, (), prefix+IND, out)
    elif isinstance(v, list):
        out.write("%s%s:\n" % (prefix, k))
        pretty_print_list(v, prefix+IND, out)
    else:
        vstr = format_value(v)
        if "\n" in vstr:
            # Multiline strings
            out.write("%s%s:\n" % (prefix, k))
            for line in vstr.splitlines(False):
                out.write("%s%s\n" % (prefix+IND, line))
        else:
            # Singleline strings
            out.write("%s%s: %s\n" % (prefix, k, vstr))


def pretty_print_list(li, prefix="", out=sys.stdout):
    listr = pprint.pformat(li)
    if len(listr) < MAXWIDTH - len(prefix) and "\\n" not in listr:
        out.write("%s%s\n" % (prefix, listr))
    else:
        for k, v in enumerate(li):
            pretty_print_item("new[%d]" % k, v, prefix, out)


def pretty_print_dict(d, exclude_keys=(), prefix="", out=sys.stdout):
    """Pretty-print a dict without wrapper keys

    Instead of {'key': 'value'}, do

        key: value
        key:
          long
          value

    """
    for k in sorted(set(d) - set(exclude_keys)):
        v = d[k]
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
    out.write("%soutput%s:\n" % (prefix, numstr))

    item_keys = ("output_type", "execution_count",
                 "name", "text", "data",
                 "ename", "evalue", "traceback")
    for k in item_keys:
        v = output.get(k)
        if v:
            pretty_print_item(k, v, oprefix, out)

    exclude_keys = {"output_type", "metadata", "traceback"} | set(item_keys)

    metadata = output.get("metadata")
    if metadata:
        known_output_metadata_keys = {"isolated"}
        pretty_print_metadata(metadata, known_output_metadata_keys, oprefix, out)

    pretty_print_dict(output, exclude_keys, oprefix, out)


def pretty_print_outputs(outputs, prefix="", out=sys.stdout):
    out.write("%soutputs:\n" % (prefix,))
    for i, output in enumerate(outputs):
        pretty_print_output(i, output, prefix+IND, out)


def pretty_print_attachments(attachments, prefix="", out=sys.stdout):
    out.write("%sattachments:\n" % (prefix,))
    for name in sorted(attachments):
        pretty_print_item(name, attachments[name], prefix+IND, out)


def pretty_print_source(source, prefix="", out=sys.stdout):
    out.write("%ssource:\n" % (prefix,))
    pretty_print_multiline(source, prefix+IND, out)


def pretty_print_cell(i, cell, prefix="", out=sys.stdout, args=None):
    key_prefix = prefix+IND

    def c():
        if not c.called:
            # Write cell type and optionally number:
            numstr = "" if i is None else " %d" % i
            out.write("%s%s cell%s:\n" % (prefix, cell.cell_type, numstr))
            c.called = True
    c.called = False

    execution_count = cell.get("execution_count")
    if execution_count and (args is None or args.details):
        # Write execution count if there (only source cells)
        c()
        out.write("%sexecution_count: %s\n" % (key_prefix, repr(cell.execution_count)))

    metadata = cell.get("metadata")
    if metadata and (args is None or args.metadata):
        # Write cell metadata
        c()
        known_cell_metadata_keys = {"collapsed", "autoscroll", "deletable", "format", "name", "tags"}
        pretty_print_metadata(cell.metadata, known_cell_metadata_keys, key_prefix, out)

    source = cell.get("source")
    if source and (args is None or args.sources):
        # Write source
        c()
        pretty_print_source(source, key_prefix, out)

    attachments = cell.get("attachments")
    if attachments and (args is None or args.attachments):
        # Write attachment if there (only markdown and raw cells)
        c()
        pretty_print_attachments(attachments, key_prefix, out)

    outputs = cell.get("outputs")
    if outputs and (args is None or args.outputs):
        # Write outputs if there (only source cells)
        c()
        pretty_print_outputs(outputs, key_prefix, out)

    exclude_keys = {'cell_type', 'source', 'execution_count', 'outputs', 'metadata', 'attachment'}
    if (set(cell) - exclude_keys) and (args is None or args.details):
        # present anything we haven't special-cased yet (future-proofing)
        c()
        pretty_print_dict(cell, exclude_keys, key_prefix, out)


def pretty_print_notebook(nb, args=None, out=sys.stdout):
    """Pretty-print a notebook for debugging, skipping large details in metadata and output

    Parameters
    ----------

    nb: dict
        The notebook object
    args: argparse Namespace or similar object
        Arguments to turn on/off showing parts of notebook, including:
        args.sources, args.outputs, args.attachments, args.metadata, args.details
    out: file-like object
        File-like object with .write function used for output.
    """

    if args is None or args.details:
        # Write notebook header
        out.write("notebook format: %d.%d\n" % (nb.nbformat, nb.nbformat_minor))

    # Report unknown keys
    unknown_keys = set(nb.keys()) - {"nbformat", "nbformat_minor", "metadata", "cells"}
    if unknown_keys:
        out.write("unknown keys: %r" % (unknown_keys,))

    if args is None or args.metadata:
        # Write notebook metadata
        known_metadata_keys = {"kernelspec"}
        pretty_print_metadata(nb.metadata, known_metadata_keys, "", out)

    # Write notebook cells
    for i, cell in enumerate(nb.cells):
        pretty_print_cell(i, cell, prefix="", out=out, args=args)
