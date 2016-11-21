# coding: utf-8

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import unicode_literals
from __future__ import print_function

from itertools import chain
import io
import os
import pprint
import re
import shutil
from subprocess import Popen, PIPE
import tempfile
from difflib import unified_diff

try:
    from textwrap import indent
except ImportError:
    def indent(text, prefix):
        """The relevant part of textwrap.indent for Python 2"""
        return prefix + text.replace('\n', '\n' + prefix)

from six import string_types

import colorama

from .diff_format import NBDiffFormatError, DiffOp
from .patching import patch
from .utils import star_path, split_path, join_path

try:
    from shutil import which
except ImportError:
    from backports.shutil_which import which

# Toggle indentation here
with_indent = False

# Change to enable/disable color print etc.
_git_diff_print_cmd = 'git diff --no-index --color-words'

# colors
REMOVE = colorama.Fore.RED + '-'
ADD = colorama.Fore.GREEN + '+'
RESET = colorama.Style.RESET_ALL


def present_dict_no_markup(prefix, d, exclude_keys=None):
    """Pretty-print a dict without wrapper keys

    Instead of {'key': 'value'}, do

        key: value
        key:
          long
          value

    """
    pp = []
    value_prefix = prefix + '  '
    for key in sorted(d):
        if exclude_keys and key in exclude_keys:
            continue
        value = d[key]
        if isinstance(value, (dict, list)):
            pp.append(prefix + key + ':')
            pp.extend(present_value(value_prefix, value))
        elif isinstance(value, string_types):
            if '\n' in value:
                pp.append(prefix + key + ':')
                pp.extend(present_value(value_prefix, value))
            else:
                pp.extend(present_value(prefix + key + ': ', value))
        else:
            pp.extend(present_value(prefix + key + ': ', value))
    return pp


_base64 = re.compile(r'^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$', re.MULTILINE|re.UNICODE)

def _trim_base64(s):
    """Trim base64 strings"""
    if len(s) > 64 and _base64.match(s.replace('\n', '')):
        s = s[:16] + '...<snip base64>...' + s[-16:].strip()
    return s

def present_multiline_string(prefix, s):
    """Present a multi-line string"""
    s = _trim_base64(s)
    return indent(s, prefix).splitlines()


def present_output(prefix, output):
    """Present an output (whole output add/delete)

    Called by present_value
    """
    pp = []
    pp.append(prefix + 'output_type: %s' % output['output_type'])
    value_prefix = prefix + '  '
    if output.get('metadata'):
        pp.append(prefix + 'metadata:')
        pp.extend(present_value(value_prefix, output['metadata']))
    if output['output_type'] in {'display_data', 'execute_result'} and 'data' in output:
        pp.append(prefix + 'data:')
        pp.extend(present_dict_no_markup(value_prefix, output['data']))

    pp.extend(present_dict_no_markup(prefix, output,
        exclude_keys={'output_type', 'metadata', 'data'},
    ))

    return pp


def present_attachment(prefix, key, mime_bundle):
    """Present an attachment (whole attachment add/delete)

    Called by present_value
    """
    pp = []
    pp.append(prefix + key + ':')
    value_prefix = prefix + '  '
    pp.extend(present_dict_no_markup(value_prefix, mime_bundle))
    return pp


def present_cell(prefix, cell):
    """Present a cell as a scalar (whole cell delete/add)

    Called by present_value
    """
    pp = []
    pp.append('')
    pp.append(prefix + "%s cell:" % cell['cell_type'])
    key_prefix = prefix + '  '
    value_prefix = prefix + '    '

    if cell.get('execution_count') is not None:
        pp.append(key_prefix + 'execution_count: %s' % cell['execution_count'])

    if cell['metadata']:
        pp.append(key_prefix + 'metadata:')
        pp.extend(present_value(value_prefix, cell['metadata']))

    pp.append(key_prefix + 'source:')
    pp.extend(present_multiline_string(value_prefix, cell['source']))

    if cell.get('outputs'):
        pp.append(key_prefix + 'outputs:')
        for output in cell['outputs']:
            pp.extend(present_output(value_prefix, output))

    if cell.get('attachments'):
        pp.append(key_prefix + 'attachments:')
        for key, mime_bundle in cell['attachments']:
            pp.extend(present_attachment(value_prefix, key, mime_bundle))

    # present_value on anything we haven't special-cased yet
    pp.extend(present_dict_no_markup(key_prefix, cell,
        exclude_keys={'cell_type', 'source', 'execution_count', 'outputs', 'metadata'},
    ))
    return pp


def present_value(prefix, arg, path=None):
    """Present a whole value that is either added or deleted.

    Calls out to other formatters for cells, outputs, and multiline strings.

    Uses pprint.pformat, otherwise.
    """
    # TODO: improve pretty-print of arbitrary values?
    if isinstance(arg, string_types):
        return present_multiline_string(prefix, arg)
    elif path is not None:
        if path.startswith('/'):
            path_prefix, path_trail = ('', path)
        else:
            path_prefix, path_trail = path.split('/', 1)
        starred = star_path(split_path(path_trail))
        if starred == '/cells/*':
            return present_cell(prefix, arg)
        elif starred == '/cells':
            return chain(*[ present_cell(prefix + '  ', cell) for cell in arg ])
        elif starred == '/cells/*/outputs/*':
            return present_output(prefix, arg)
        elif starred == '/cells/*/outputs':
            return chain(*[ present_output(prefix + '  ', out) for out in arg ])
        elif starred == '/cells/*/attachments':
            return chain(*[ present_attachment(prefix + '  ', key, bundle) for (key, bundle) in arg.items() ])

    lines = pprint.pformat(arg).splitlines()
    return [prefix + line for line in lines]


def present_dict_diff(a, di, path):
    "Pretty-print a nbdime diff."
    pp = []

    di = {e.key: e for e in di}
    for key in sorted(di):
        e = di[key]

        op = e.op
        assert key == e.key

        nextpath = "/".join((path, key))

        if op == DiffOp.REMOVE:
            pp.append("delete from {}:".format(nextpath))
            pp += present_value(REMOVE, a[key], nextpath)

        elif op == DiffOp.ADD:
            pp.append("insert at {}:".format(nextpath))
            pp += present_value(ADD, e.value, nextpath)

        elif op == DiffOp.REPLACE:
            pp.append("replace at {}:".format(nextpath))
            pp += present_value(REMOVE, a[key], nextpath)
            pp += present_value(ADD, e.value, nextpath)

        elif op == DiffOp.PATCH:
            if with_indent:
                pp.append("patch {}:".format(nextpath))
            pp += present_diff(a[key], e.diff, nextpath)

        else:
            raise NBDiffFormatError("Unknown dict diff op {}".format(op))
        if pp:
            pp[-1] += RESET

    return pp


def present_list_diff(a, d, path):
    "Pretty-print a nbdime diff."
    pp = []
    for e in d:
        op = e.op
        index = e.key

        nextpath = "/".join((path, str(index)))

        if op == DiffOp.ADDRANGE:
            pp.append("insert before {}:".format(nextpath))
            pp += present_value(ADD, e.valuelist, nextpath)

        elif op == DiffOp.REMOVERANGE:
            if e.length > 1:
                r = "{}-{}".format(index, index + e.length - 1)
            else:
                r = str(index)
            pp.append("delete {}/{}:".format(path, r))
            pp += present_value(REMOVE, a[index: index + e.length], nextpath)

        elif op == DiffOp.PATCH:
            if with_indent:
                pp.append("patch {}:".format(nextpath))
            pp += present_diff(a[index], e.diff, nextpath)

        else:
            raise NBDiffFormatError("Unknown list diff op {}".format(op))
        if pp:
            pp[-1] += RESET

    return pp


def present_string_diff(a, di, path):
    "Pretty-print a nbdime diff."

    header = []
    if not with_indent:
        # if we are indenting each level, this is redunant
        header.append("patch {}:".format(path))

    if _base64.match(a):
        return header + ['<base64 data changed>']

    b = patch(a, di)
    cmd = None
    if which('git'):
        cmd = _git_diff_print_cmd.split()
        heading_lines = 4
    elif which('diff'):
        cmd = ['diff']
        heading_lines = 0
    else:
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
        heading_lines = 2

    if cmd is not None:
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
    return header + diff.splitlines()[heading_lines:]


def present_diff(a, di, path, indent=True):
    "Pretty-print a nbdime diff."
    if isinstance(a, dict):
        pp = present_dict_diff(a, di, path)
    elif isinstance(a, list):
        pp = present_list_diff(a, di, path)
    elif isinstance(a, string_types):
        pp = present_string_diff(a, di, path)
    else:
        raise NBDiffFormatError("Invalid type {} for diff presentation.".format(type(a)))

    # Optionally indent
    if with_indent:
        indsep = " "*2
        return [indsep + line for line in pp] if indent else pp
    else:
        return pp


header = """\
nbdiff {afn} {bfn}
--- a: {afn}
+++ b: {bfn}
"""


def pretty_print_notebook_diff(afn, bfn, a, di):
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
    p = present_diff(a, di, path="a", indent=False)
    if p:
        p = [header.format(afn=afn, bfn=bfn)] + p
    print("\n".join(p))
