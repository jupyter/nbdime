# coding: utf-8

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import unicode_literals
from __future__ import print_function

from itertools import chain
import os
import pprint
import re
import shutil
from subprocess import Popen, PIPE
import tempfile
try:
    from textwrap import indent
except ImportError:
    def indent(text, prefix):
        """The relevant part of textwrap.indent for Python 2"""
        return prefix + text.replace('\n', '\n' + prefix)

from six import string_types

from .diff_format import NBDiffFormatError, Diff
from .patching import patch

try:
    from shutil import which
except ImportError:
    from backports.shutil_which import which

# Toggle indentation here
with_indent = True


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
                pp.append(prefix + '%s: %s' % (key, value))
        else:
            pp.append(prefix + '%s: %s' % (key,  value))
    return pp


_base64 = re.compile(r'^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$', re.MULTILINE|re.UNICODE)

def _trim_base64(s):
    """Trim base64 strings"""
    if len(s) > 64 and _base64.match(s):
        s = s[:16] + '...<snip base64>...' + s[-16:].strip()
    return s

def present_multiline_string(prefix, s):
    """Present a multi-line string"""
    s = _trim_base64(s)
    return indent(s, prefix).splitlines()


def present_output(prefix, output):
    """Present an output (whole output add/delete)"""
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


def present_cell(prefix, cell):
    """Present a cell as a scalar (whole cell delete/add)"""
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

    # present_value on anything we haven't special-cased yet
    pp.extend(present_dict_no_markup(key_prefix, cell,
        exclude_keys={'cell_type', 'source', 'execution_count', 'outputs', 'metadata'},
    ))
    return pp

def present_value(prefix, arg):
    # TODO: improve pretty-print of arbitrary values?
    if isinstance(arg, dict):
        if 'cell_type' in arg:
            return present_cell(prefix, arg)
        elif 'output_type' in arg:
            return present_output(prefix, arg)
    elif isinstance(arg, list) and arg:
        first = arg[0]
        if isinstance(first, dict):
            if 'cell_type' in first:
                return chain(*[ present_cell(prefix + '  ', cell) for cell in arg ])
            elif 'output_type' in first:
                return chain(*[ present_output(prefix + '  ', out) for out in arg ])
    elif isinstance(arg, string_types):
        return present_multiline_string(prefix, arg)

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

        if op == Diff.REMOVE:
            pp.append("delete from {}:".format(nextpath))
            pp += present_value("- ", a[key])

        elif op == Diff.ADD:
            pp.append("insert at {}:".format(nextpath))
            pp += present_value("+ ", e.value)

        elif op == Diff.REPLACE:
            pp.append("replace at {}:".format(nextpath))
            pp += present_value("- ", a[key])
            pp += present_value(" +", e.value)

        elif op == Diff.PATCH:
            if with_indent:
                pp.append("patch {}:".format(nextpath))
            pp += present_diff(a[key], e.diff, nextpath)

        else:
            raise NBDiffFormatError("Unknown dict diff op {}".format(op))

    return pp


def present_list_diff(a, d, path):
    "Pretty-print a nbdime diff."
    pp = []
    for e in d:
        op = e.op
        index = e.key

        nextpath = "/".join((path, str(index)))

        if op == Diff.ADDRANGE:
            pp.append("insert before {}:".format(nextpath))
            pp += present_value("+ ", e.valuelist)

        elif op == Diff.REMOVERANGE:
            if e.length > 1:
                r = "{}-{}".format(index, index + e.length - 1)
            else:
                r = str(index)
            pp.append("delete {}/{}:".format(path, r))
            pp += present_value("- ", a[index: index + e.length])

        elif op == Diff.PATCH:
            if with_indent:
                pp.append("patch {}:".format(nextpath))
            pp += present_diff(a[index], e.diff, nextpath)

        else:
            raise NBDiffFormatError("Unknown list diff op {}".format(op))

    return pp

def present_string_diff(a, di, path):
    "Pretty-print a nbdime diff."
    if _base64.match(a):
        return ['<base64 data changed>']
    b = patch(a, di)
    td = tempfile.mkdtemp()
    try:
        with open(os.path.join(td, 'before'), 'w') as f:
            f.write(a)
        with open(os.path.join(td, 'after'), 'w') as f:
            f.write(b)
        print(which)
        if which('git'):
            cmd = 'git diff --no-index --color-words'.split()
            heading_lines = 4
        else:
            cmd = ['diff']
            heading_lines = 0
        p = Popen(cmd + ['before', 'after'], cwd=td, stdout=PIPE)
        out, _ = p.communicate()
        dif = out.decode('utf8')
    finally:
        shutil.rmtree(td)
    return dif.splitlines()[heading_lines:]

    consumed = 0
    lines = []
    continuation = False
    continuation_indent = 0
    continuation_indent2 = 0
    for e in di:
        op = e.op
        index = e.key

        # Consume untouched characters
        if index > consumed:
            dlines = a[consumed:index].split("\n")
            for dline in dlines:
                prefix = ".." if continuation else "  "
                lines.append(prefix + " "*continuation_indent2 + dline)
                continuation = False
                continuation_indent2 = 0
            continuation_indent = len(lines[-1]) - 2
            continuation_indent2 = continuation_indent
            consumed = index

        if op == Diff.ADDRANGE:
            dlines = e.valuelist.split("\n")
            lines.append("+ " + " "*continuation_indent + dlines[0])
            for dline in dlines[1:]:
                lines.append("+ " + dline)
            continuation = True
            continuation_indent2 = max(continuation_indent2, len(lines[-1]) - 2)

        elif op == Diff.REMOVERANGE:
            dlines = a[index: index + e.length].split("\n")
            lines.append("- " + " "*continuation_indent + dlines[0])
            for dline in dlines[1:]:
                lines.append("- " + dline)
            consumed = index + e.length
            continuation = True
            continuation_indent2 = max(continuation_indent2, len(lines[-1]) - 2)

        else:
            raise NBDiffFormatError("Unknown string diff op {}".format(op))

    # Consume untouched characters at end
    index = len(a)  # copy-paste from top of loop...
    if index > consumed:
        dlines = a[consumed:index].split("\n")
        for dline in dlines:
            prefix = ".." if continuation else "  "
            lines.append(prefix + " "*continuation_indent2 + dline)
            continuation = False
            continuation_indent2 = 0
        continuation_indent = len(lines[-1]) - 2
        continuation_indent2 = continuation_indent
        consumed = index

    return lines


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
