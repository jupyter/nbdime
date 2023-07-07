# -*- coding: utf-8 -*-

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from collections import namedtuple
import datetime
from difflib import unified_diff
import hashlib
import io
import os
import pprint
import re
import shutil
from subprocess import Popen, PIPE
import sys
import tempfile

from shutil import which

import colorama

from .diff_format import NBDiffFormatError, DiffOp, op_patch
from .ignorables import diff_ignorables
from .patching import patch
from .utils import star_path, split_path, join_path
from .utils import as_text, as_text_lines
from .log import warning


# Indentation offset in pretty-print
IND = "  "

# Max line width used some placed in pretty-print
# TODO: Use this for line wrapping some places?
MAXWIDTH = 78

git_diff_print_cmd = 'git diff --no-index --color-words before after'
diff_print_cmd = 'diff before after'
git_mergefile_print_cmd = 'git merge-file -p local base remote'
diff3_print_cmd = 'diff3 -m local base remote'


DIFF_ENTRY_END = '\n'

ColoredConstants = namedtuple('ColoredConstants', (
    'KEEP',
    'REMOVE',
    'ADD',
    'INFO',
    'RESET',
))


col_const = {
    True: ColoredConstants(
        KEEP   = '{color}   '.format(color=''),
        REMOVE = '{color}-  '.format(color=colorama.Fore.RED),
        ADD    = '{color}+  '.format(color=colorama.Fore.GREEN),
        INFO   = '{color}## '.format(color=colorama.Fore.BLUE + colorama.Style.BRIGHT),
        RESET  = colorama.Style.RESET_ALL,
    ),

    False: ColoredConstants(
        KEEP   = '   ',
        REMOVE = '-  ',
        ADD    = '+  ',
        INFO   = '## ',
        RESET  = '',
    )
}


class PrettyPrintConfig:
    def __init__(
            self,
            out=sys.stdout,
            include=None,
            color_words=False,
            use_git = True,
            use_diff = True,
            use_color = True,
            language = None
            ):
        self.out = out
        if include is None:
            for key in diff_ignorables:
                setattr(self, key, True)
        else:
            for key in diff_ignorables:
                setattr(self, key, getattr(include, key, True))

        self.color_words = color_words

        self.use_git = use_git
        self.use_diff = use_diff
        self.use_color = use_color
        self.language = language

    def should_ignore_path(self, path):
        starred = star_path(split_path(path))
        if starred.startswith('/cells/*/source'):
            return not self.sources
        if starred.startswith('/cells/*/attachments'):
            return not self.attachments
        if starred.startswith('/cells/*/metadata') or starred.startswith('/metadata'):
            return not self.metadata
        if starred.startswith('/cells/*/id'):
            return not self.id
        if starred.startswith('/cells/*/outputs'):
            return (
                not self.outputs or
                (starred == '/cells/*/outputs/*/execution_count' and
                 not self.details))
        # Can check against '/cells/*/' since we've processed all other
        # sub-keys that we know about above.
        if starred.startswith('/cells/*/'):
            return not self.details
        if starred.startswith('/nbformat'):
            return not self.details
        return False

    @property
    def KEEP(self):
        return col_const[self.use_color].KEEP

    @property
    def REMOVE(self):
        return col_const[self.use_color].REMOVE

    @property
    def ADD(self):
        return col_const[self.use_color].ADD

    @property
    def INFO(self):
        return col_const[self.use_color].INFO

    @property
    def RESET(self):
        return col_const[self.use_color].RESET

DefaultConfig = PrettyPrintConfig()


def external_merge_render(cmd, b, l, r):
    b = as_text(b)
    l = as_text(l)
    r = as_text(r)
    td = tempfile.mkdtemp()
    try:
        with io.open(os.path.join(td, 'local'), 'w', encoding="utf8") as f:
            f.write(l)
        with io.open(os.path.join(td, 'base'), 'w', encoding="utf8") as f:
            f.write(b)
        with io.open(os.path.join(td, 'remote'), 'w', encoding="utf8") as f:
            f.write(r)
        assert all(fn in cmd for fn in ['local', 'base', 'remote']), (
            'invalid cmd argument for external merge renderer')
        p = Popen(cmd, cwd=td, stdout=PIPE)
        output, errors = p.communicate()
        status = p.returncode
        output = output.decode('utf8')
        # normalize newlines
        output = output.replace('\r\n', '\n')
    finally:
        shutil.rmtree(td)
    return output, status


def external_diff_render(cmd, a, b):
    a = as_text(a)
    b = as_text(b)
    td = tempfile.mkdtemp()
    try:
        # TODO: Pass in language information so that an appropriate file
        # extension can be used. This should provide a hint to the differ.
        with io.open(os.path.join(td, 'before'), 'w', encoding="utf8") as f:
            f.write(a)
        with io.open(os.path.join(td, 'after'), 'w', encoding="utf8") as f:
            f.write(b)
        assert all(fn in cmd for fn in ['before', 'after']), (
            'invalid cmd argument for external diff renderer: %r' %
            cmd)
        p = Popen(cmd, cwd=td, stdout=PIPE)
        output, errors = p.communicate()
        status = p.returncode
        output = output.decode('utf8')
        r = re.compile(r"^\\ No newline at end of file\n?", flags=re.M)
        output, n = r.subn("", output)
        assert n <= 2, 'unexpected output from external diff renderer'
    finally:
        shutil.rmtree(td)
    return output, status


def format_merge_render_lines(
        base, local, remote,
        base_title, local_title, remote_title,
        marker_size, include_base):
    sep0 = "<"*marker_size
    sep1 = "|"*marker_size
    sep2 = "="*marker_size
    sep3 = ">"*marker_size

    if local and local[-1].endswith('\n'):
        local[-1] = local[-1] + '\n'
    if remote and remote[-1].endswith('\n'):
        remote[-1] = remote[-1] + '\n'

    # Extract equal lines at beginning
    prelines = []
    i = 0
    n = min(len(local), len(remote))
    while i < n and local[i] == remote[i]:
        prelines.append(local[i])
        i += 1
    local = local[i:]
    remote = remote[i:]

    # Extract equal lines at end
    postlines = []
    i = len(local) - 1
    j = len(remote) - 1
    while (i >= 0 and i < len(local) and
           j >= 0 and j < len(remote) and
           local[i] == remote[j]):
        postlines.append(local[i])
        i += 1
        j += 1
    postlines = reversed(postlines)
    local = local[:i+1]
    remote = remote[:j+1]

    lines = []
    lines.extend(prelines)

    sep0 = "%s %s\n" % (sep0, local_title)
    lines.append(sep0)
    lines.extend(local)

    # This doesn't take prelines and postlines into account
    # if include_base:
    #     sep1 = "%s %s\n" % (sep1, base_title)
    #     lines.append(sep1)
    #     lines.extend(base)

    sep2 = "%s\n" % (sep2,)
    lines.append(sep2)
    lines.extend(remote)

    sep3 = "%s %s\n" % (sep3, remote_title)
    lines.append(sep3)

    lines.extend(postlines)

    # Make sure all but the last line ends with newline
    for i in range(len(lines)):
        if not lines[i].endswith('\n'):
            lines[i] = lines[i] + '\n'
    if lines:
        lines[-1] = lines[-1].rstrip("\r\n")

    return lines


def builtin_merge_render(base, local, remote, strategy=None):
    if local == remote:
        return local, 0

    # In this extremely simplified merge rendering,
    # we currently define conflict as local != remote

    if strategy == "use-local":
        return local, 0
    elif strategy == "use-remote":
        return remote, 0
    elif strategy is not None:
        warning("Using builtin merge render but ignoring strategy %s", strategy)

    # Styling
    local_title = "local"
    base_title = "base"
    remote_title = "remote"
    marker_size = 7  # git uses 7 by default

    include_base = False  # TODO: Make option

    local = as_text_lines(local)
    base = as_text_lines(base)
    remote = as_text_lines(remote)

    lines = format_merge_render_lines(
        base, local, remote,
        base_title, local_title, remote_title,
        marker_size, include_base
        )

    merged = "".join(lines)
    return merged, 1


def builtin_diff_render(a, b, config):
    gen = unified_diff(
        a.splitlines(False),
        b.splitlines(False),
        lineterm='')
    uni = []
    for line in gen:
        if line.startswith('+'):
            uni.append("%s%s%s" % (config.ADD, line[1:], config.RESET))
        elif line.startswith('-'):
            uni.append("%s%s%s" % (config.REMOVE, line[1:], config.RESET))
        elif line.startswith(' '):
            uni.append("%s%s%s" % (config.KEEP, line[1:], config.RESET))
        elif line.startswith('@'):
            uni.append(line)
        else:
            # Don't think this will happen?
            uni.append("%s%s%s" % (config.KEEP, line[1:], config.RESET))
    return '\n'.join(uni)


def diff_render_with_git(a, b, config):
    cmd = git_diff_print_cmd
    if not config.use_color:
        cmd = cmd.replace(" --color-words", "")
    elif not config.color_words:
        # Will do nothing if use_color is not True:
        cmd = cmd.replace("--color-words", "--color")
    diff, status = external_diff_render(cmd.split(), a, b)
    return "".join(diff.splitlines(True)[4:])


def diff_render_with_diff(a, b):
    cmd = diff_print_cmd
    diff, status = external_diff_render(cmd.split(), a, b)
    return diff


def diff_render_with_difflib(a, b, config):
    diff = builtin_diff_render(a, b, config)
    return "".join(diff.splitlines(True)[2:])


def diff_render(a, b, config=DefaultConfig):
    if config.use_git and which('git'):
        return diff_render_with_git(a, b, config)
    elif config.use_diff and which('diff'):
        return diff_render_with_diff(a, b)
    else:
        return diff_render_with_difflib(a, b, config)


def merge_render_with_git(b, l, r, strategy=None):
    # Note: git merge-file also takes argument -L to change label if needed
    cmd = git_mergefile_print_cmd
    if strategy == "use-local":
        cmd += " --ours"
    elif strategy == "use-remote":
        cmd += " --theirs"
    elif strategy == "union":
        cmd += " --union"
    elif strategy is not None:
        warning("Using git merge-file but ignoring strategy %s", strategy)
    merged, status = external_merge_render(cmd.split(), b, l, r)

    # Remove trailing newline if ">>>>>>> remote" is the last line
    lines = merged.splitlines(True)
    if "\n" in lines[-1] and (">"*7) in lines[-1]:
        merged = merged.rstrip()
    return merged, status


def merge_render_with_diff3(b, l, r, strategy=None):
    # Note: diff3 also takes argument -L to change label if needed
    cmd = diff3_print_cmd
    if strategy == "use-local":
        return l, 0
    elif strategy == "use-remote":
        return r, 0
    elif strategy is not None:
        warning("Using diff3 but ignoring strategy %s", strategy)
    merged, status = external_merge_render(cmd.split(), b, l, r)
    return merged, status


def merge_render(b, l, r, strategy=None, config=DefaultConfig):
    if strategy == "use-base":
        return b, 0
    if config.use_git and which('git'):
        return merge_render_with_git(b, l, r, strategy)
    elif config.use_diff and which('diff3'):
        return merge_render_with_diff3(b, l, r, strategy)
    else:
        return builtin_merge_render(b, l, r, strategy)


def file_timestamp(filename):
    "Return modification time for filename as a string."
    if os.path.exists(filename):
        t = os.path.getmtime(filename)
        dt = datetime.datetime.fromtimestamp(t)
        return dt.isoformat(str(" "))
    else:
        return "(no timestamp)"


def hash_string(s):
    return hashlib.md5(s.encode("utf8")).hexdigest()

_base64 = re.compile(
    r'^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$',
    re.MULTILINE | re.UNICODE)

def _trim_base64(s):
    """Trim and hash base64 strings"""
    if len(s) > 64 and _base64.match(s.replace('\n', '')):
        h = hash_string(s)
        s = '%s...<snip base64, md5=%s...>' % (s[:8], h[:16])
    return s


def format_value(v):
    "Format simple value for printing. Snips base64 strings and uses pprint for the rest."
    if not isinstance(v, str):
        # Not a string, defer to pprint
        vstr = pprint.pformat(v)
    else:
        # Snip if base64 data
        vstr = _trim_base64(v)
    return vstr


def pretty_print_value(value, prefix="", config=DefaultConfig):
    """Print a possibly complex value with all lines prefixed.

    Calls out to generic formatters based on value
    type for dicts, lists, and multiline strings.
    Uses format_value for simple values.
    """
    if isinstance(value, dict):
        pretty_print_dict(value, (), prefix, config)
    elif isinstance(value, list) and value:
        pretty_print_list(value, prefix, config)
    else:
        pretty_print_multiline(format_value(value), prefix, config)


def pretty_print_value_at(value, path, prefix="", config=DefaultConfig):
    """Print a possibly complex value with all lines prefixed.

    Calls out to other specialized formatters based on path
    for cells, outputs, attachments, and more generic formatters
    based on type for dicts, lists, and multiline strings.
    Uses format_value for simple values.
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
            pretty_print_cell(None, value, prefix, True, config)
        elif starred == "/cells":
            for cell in value:
                pretty_print_cell(None, cell, prefix, True, config)
        elif starred == "/cells/*/outputs/*":
            pretty_print_output(None, value, prefix, config)
        elif starred == "/cells/*/outputs":
            for output in value:
                pretty_print_output(None, output, prefix, config)
        elif starred == "/cells/*/attachments":
            pretty_print_attachments(value, prefix, config)
        else:
            starred = None

    if starred is None:
        pretty_print_value(value, prefix, config)


def pretty_print_key(k, prefix, config):
    config.out.write("%s%s:\n" % (prefix, k))


def pretty_print_key_value(k, v, prefix, config):
    config.out.write("%s%s: %s\n" % (prefix, k, v))


def pretty_print_diff_action(msg, path, config):
    config.out.write("%s%s %s:%s\n" % (config.INFO, msg, path, config.RESET))


def pretty_print_item(k, v, prefix="", config=DefaultConfig):
    if isinstance(v, dict):
        pretty_print_key(k, prefix, config)
        pretty_print_dict(v, (), prefix+IND, config)
    elif isinstance(v, list):
        pretty_print_key(k, prefix, config)
        pretty_print_list(v, prefix+IND, config)
    else:
        vstr = format_value(v)
        if "\n" in vstr:
            # Multiline strings
            pretty_print_key(k, prefix, config)
            for line in vstr.splitlines(False):
                config.out.write("%s%s\n" % (prefix+IND, line))
        else:
            # Singleline strings
            pretty_print_key_value(k, vstr, prefix, config)


def pretty_print_multiline(text, prefix="", config=DefaultConfig):
    assert isinstance(text, str), 'expected string argument'

    # Preprend prefix to lines, letting lines keep their own newlines
    lines = text.splitlines(True)
    for line in lines:
        config.out.write(prefix + line)

    # If the final line doesn't have a newline,
    # make sure we still start a new line
    if not text.endswith("\n"):
        config.out.write("\n")


def pretty_print_list(li, prefix="", config=DefaultConfig):
    listr = pprint.pformat(li)
    if len(listr) < MAXWIDTH - len(prefix) and "\\n" not in listr:
        config.out.write("%s%s\n" % (prefix, listr))
    else:
        for k, v in enumerate(li):
            pretty_print_item("item[%d]" % k, v, prefix, config)


def pretty_print_dict(d, exclude_keys=(), prefix="", config=DefaultConfig):
    """Pretty-print a dict without wrapper keys

    Instead of {'key': 'value'}, do

        key: value
        key:
          long
          value

    """
    for k in sorted(set(d) - set(exclude_keys)):
        v = d[k]
        pretty_print_item(k, v, prefix, config)


def pretty_print_metadata(md, known_keys, prefix="", config=DefaultConfig):
    md1 = {}
    md2 = {}
    for k in md:
        if k in known_keys:
            md1[k] = md[k]
        else:
            md2[k] = md[k]
    if md1:
        pretty_print_key("metadata (known keys)", prefix, config)
        pretty_print_dict(md1, (), prefix+IND, config)
    if md2:
        pretty_print_key("metadata (unknown keys)", prefix, config)
        pretty_print_dict(md2, (), prefix+IND, config)


def pretty_print_output(i, output, prefix="", config=DefaultConfig):
    oprefix = prefix+IND
    numstr = "" if i is None else " %d" % i
    k = "output%s" % (numstr,)
    pretty_print_key(k, prefix, config)

    item_keys = ("output_type", "execution_count",
                 "name", "text", "data",
                 "ename", "evalue", "traceback")
    for k in item_keys:
        v = output.get(k)
        if v:
            pretty_print_item(k, v, oprefix, config)

    exclude_keys = {"output_type", "metadata", "traceback"} | set(item_keys)

    metadata = output.get("metadata")
    if metadata:
        known_output_metadata_keys = {"isolated"}
        pretty_print_metadata(metadata, known_output_metadata_keys, oprefix, config)

    pretty_print_dict(output, exclude_keys, oprefix, config)


def pretty_print_outputs(outputs, prefix="", config=DefaultConfig):
    pretty_print_key("outputs", prefix, config)
    for i, output in enumerate(outputs):
        pretty_print_output(i, output, prefix+IND, config)


def pretty_print_attachments(attachments, prefix="", config=DefaultConfig):
    pretty_print_key("attachments", prefix, config)
    for name in sorted(attachments):
        pretty_print_item(name, attachments[name], prefix+IND, config)

try:
    from pygments import highlight
    from pygments.formatters import Terminal256Formatter
    from pygments.lexers import find_lexer_class_by_name
    from pygments.util import ClassNotFound

    def colorize_source(source, lexer_name):
        try:
            lexer = find_lexer_class_by_name(lexer_name)()
        except ClassNotFound:
            return source
        formatter = Terminal256Formatter()
        return highlight(source, lexer, formatter)

except ImportError as e:
    def colorize_source(source, *args, **kwargs):
        return source


def pretty_print_source(source, prefix="", is_markdown=False, config=DefaultConfig):
    pretty_print_key("source", prefix, config)
    if not prefix.strip() and (is_markdown or config.language):
        source_highlighted = colorize_source(
            source,
            'markdown' if is_markdown else config.language
        )
    else:
        source_highlighted = source
    pretty_print_multiline(source_highlighted, prefix+IND, config)


def pretty_print_cell(i, cell, prefix="", force_header=False, config=DefaultConfig):
    key_prefix = prefix+IND

    def c():
        "Write cell header first time this is called."
        if not c.called:
            # Write cell type and optionally number:
            numstr = "" if i is None else " %d" % i
            k = "%s cell%s" % (cell.get("cell_type"), numstr)
            pretty_print_key(k, prefix, config)
            c.called = True
    c.called = False

    if force_header:
        c()

    id = cell.get("id")
    if id and config.details:
        # Write cell ID if there
        c()
        pretty_print_item("id", id, key_prefix, config)

    execution_count = cell.get("execution_count")
    if execution_count and config.details:
        # Write execution count if there (only source cells)
        c()
        pretty_print_item("execution_count", execution_count, key_prefix, config)

    metadata = cell.get("metadata")
    if metadata and config.metadata:
        # Write cell metadata
        c()
        known_cell_metadata_keys = {
            "collapsed", "autoscroll", "deletable", "format", "name", "tags",
        }
        pretty_print_metadata(
            cell.metadata,
            known_cell_metadata_keys,
            key_prefix,
            config)

    source = cell.get("source")
    if source and config.sources:
        is_markdown = cell.get('cell_type', None) == 'markdown'
        # Write source
        c()
        pretty_print_source(source, key_prefix, is_markdown=is_markdown, config=config)

    attachments = cell.get("attachments")
    if attachments and config.attachments:
        # Write attachment if there (only markdown and raw cells)
        c()
        pretty_print_attachments(attachments, key_prefix, config)

    outputs = cell.get("outputs")
    if outputs and config.outputs:
        # Write outputs if there (only source cells)
        c()
        pretty_print_outputs(outputs, key_prefix, config)

    exclude_keys = {
        'cell_type', 'source', 'execution_count', 'outputs', 'metadata',
        'id', 'attachment',
    }
    if (set(cell) - exclude_keys) and config.details:
        # present anything we haven't special-cased yet (future-proofing)
        c()
        pretty_print_dict(cell, exclude_keys, key_prefix, config)


def pretty_print_notebook(nb, config=DefaultConfig):
    """Pretty-print a notebook for debugging, skipping large details in metadata and output

    Parameters
    ----------

    nb: dict
        The notebook object
    config: PrettyPrintConfig
        A config object determining what is printed and where
    """
    prefix = ""

    if config.language is None:
        language_info = nb.metadata.get('language_info', {})
        config.language = language_info.get(
            'pygments_lexer',
            language_info.get('name', None)
        )

    if config.details:
        # Write notebook header
        v = "%d.%d" % (nb.nbformat, nb.nbformat_minor)
        pretty_print_key_value("notebook format", v, prefix, config)

    # Report unknown keys
    unknown_keys = set(nb.keys()) - {"nbformat", "nbformat_minor", "metadata", "cells"}
    if unknown_keys:
        pretty_print_key_value("unknown keys", repr(unknown_keys), prefix, config)

    if config.metadata:
        # Write notebook metadata
        known_metadata_keys = {"kernelspec", "language_info"}
        pretty_print_metadata(nb.metadata, known_metadata_keys, "", config)

    # Write notebook cells
    for i, cell in enumerate(nb.cells):
        pretty_print_cell(i, cell, prefix="", config=config)


def pretty_print_diff_entry(a, e, path, config=DefaultConfig):
    if config.should_ignore_path(path):
        return
    key = e.key
    nextpath = "/".join((path, str(key)))
    op = e.op

    # Recurse to handle patch ops
    if op == DiffOp.PATCH:
        # Useful for debugging:
        #if not (len(e.diff) == 1 and e.diff[0].op == DiffOp.PATCH):
        #    config.out.write("{}// patch -+{} //{}\n".format(INFO, nextpath, RESET))
        #else:
        #    config.out.write("{}// patch... -+{} //{}\n".format(INFO, nextpath, RESET))
        pretty_print_diff(a[key], e.diff, nextpath, config)
        return

    if op == DiffOp.ADDRANGE:
        pretty_print_diff_action("inserted before", nextpath, config)
        pretty_print_value_at(e.valuelist, path, config.ADD, config)

    elif op == DiffOp.REMOVERANGE:
        if e.length > 1:
            keyrange = "{}-{}".format(nextpath, key + e.length - 1)
        else:
            keyrange = nextpath
        pretty_print_diff_action("deleted", keyrange, config)
        pretty_print_value_at(a[key: key + e.length], path, config.REMOVE, config)

    elif op == DiffOp.REMOVE:
        if config.should_ignore_path(nextpath):
            return
        pretty_print_diff_action("deleted", nextpath, config)
        pretty_print_value_at(a[key], nextpath, config.REMOVE, config)

    elif op == DiffOp.ADD:
        if config.should_ignore_path(nextpath):
            return
        pretty_print_diff_action("added", nextpath, config)
        pretty_print_value_at(e.value, nextpath, config.ADD, config)

    elif op == DiffOp.REPLACE:
        if config.should_ignore_path(nextpath):
            return
        aval = a[key]
        bval = e.value
        if type(aval) is not type(bval):
            typechange = " (type changed from %s to %s)" % (
                aval.__class__.__name__, bval.__class__.__name__)
        else:
            typechange = ""
        pretty_print_diff_action("replaced" + typechange, nextpath, config)
        pretty_print_value_at(aval, nextpath, config.REMOVE, config)
        pretty_print_value_at(bval, nextpath, config.ADD, config)

    else:
        raise NBDiffFormatError("Unknown list diff op {}".format(op))

    config.out.write(DIFF_ENTRY_END + config.RESET)


def pretty_print_dict_diff(a, di, path, config=DefaultConfig):
    "Pretty-print a nbdime diff."
    for key, e in sorted([(e.key, e) for e in di], key=lambda x: x[0]):
        pretty_print_diff_entry(a, e, path, config)


def pretty_print_list_diff(a, di, path, config=DefaultConfig):
    "Pretty-print a nbdime diff."
    for e in di:
        pretty_print_diff_entry(a, e, path, config)


def pretty_print_string_diff(a, di, path, config=DefaultConfig):
    "Pretty-print a nbdime diff."
    pretty_print_diff_action("modified", path, config)

    b = patch(a, di)

    ta = _trim_base64(a)
    tb = _trim_base64(b)

    if ta != a or tb != b:
        if ta != a:
            config.out.write('%s%s\n' % (config.REMOVE, ta))
        else:
            pretty_print_value_at(a, path, config.REMOVE, config)
        if tb != b:
            config.out.write('%s%s\n' % (config.ADD, tb))
        else:
            pretty_print_value_at(b, path, config.ADD, config)
    elif "\n" in a or "\n" in b:
        # Delegate multiline diff formatting
        diff = diff_render(a, b, config)
        config.out.write(diff)
    else:
        # Just show simple -+ single line (usually metadata values etc)
        config.out.write("%s%s\n" % (config.REMOVE, a))
        config.out.write("%s%s\n" % (config.ADD, b))

    config.out.write(DIFF_ENTRY_END + config.RESET)


def pretty_print_diff(a, di, path, config=DefaultConfig):
    "Pretty-print a nbdime diff."
    if isinstance(a, dict):
        pretty_print_dict_diff(a, di, path, config)
    elif isinstance(a, list):
        pretty_print_list_diff(a, di, path, config)
    elif isinstance(a, str):
        pretty_print_string_diff(a, di, path, config)
    else:
        raise NBDiffFormatError(
            "Invalid type {} for diff presentation.".format(type(a))
        )


notebook_diff_header = """\
nbdiff {afn} {bfn}
--- {afn}{atime}
+++ {bfn}{btime}
"""

def pretty_print_notebook_diff(afn, bfn, a, di, config=DefaultConfig):
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
    config: PrettyPrintConfig
        Config object determining what gets printed and where
    """
    if di:
        path = ""
        atime = "  " + file_timestamp(afn)
        btime = "  " + file_timestamp(bfn)
        config.out.write(notebook_diff_header.format(
            afn=afn, bfn=bfn, atime=atime, btime=btime))
        pretty_print_diff(a, di, path, config)


def pretty_print_merge_decision(base, decision, config=DefaultConfig):
    prefix = IND

    path = join_path(decision.common_path)
    confnote = "conflicted " if decision.conflict else ""
    config.out.write("%s%sdecision at %s:%s\n" % (
        config.INFO.replace("##", "===="), confnote, path, config.RESET))

    diff_keys = ("diff", "local_diff", "remote_diff", "custom_diff", "similar_insert")
    exclude_keys = set(diff_keys) | {"common_path", "action", "conflict"}
    pretty_print_dict(decision, exclude_keys, prefix, config)

    for dkey in diff_keys:
        diff = decision.get(dkey)

        if (dkey == "remote_diff" and decision.action == "either" and
                diff == decision.get("local_diff")):
            # Skip remote diff
            continue
        elif (dkey == "local_diff" and decision.action == "either" and
                diff == decision.get("remote_diff")):
            note = " (same as remote_diff)"
        elif dkey.startswith(decision.action):
            note = " (selected)"
        else:
            note = ""

        if diff:
            config.out.write("%s%s%s:%s\n" % (
                config.INFO.replace("##", "---"), dkey, note, config.RESET))
            value = base
            for i, k in enumerate(decision.common_path):
                if isinstance(value, str):
                    # Example case:
                    #   common_path = /cells/0/source/3
                    #   value = nb.cells[0].source
                    #   k = line number 3
                    #   k is last item in common_path
                    assert i == len(decision.common_path) - 1, (
                        'invalid discision common path, tries to subindex string: %r' %
                        decision.common_path)

                    # Diffs on strings are usually line-based, _except_
                    # when common_path points to a line within a string.
                    # Wrap character based diff in a patch op with line
                    # number to normalize.
                    diff = [op_patch(k, diff)]
                    break
                else:
                    # Either a list or dict, get subvalue
                    value = value[k]
            pretty_print_diff(value, diff, path, config)


#def pretty_print_string_diff(string, lineno, diff, config):
#    line = string.splitlines(True)[lineno]
#    pretty_print_diff_entry(e)


def pretty_print_merge_decisions(base, decisions, config=DefaultConfig):
    """Pretty-print notebook merge decisions

    Parameters
    ----------

    base: dict
        The base notebook object
    decisions: list
        The list of merge decisions
    """
    conflicted = [d for d in decisions if d.conflict]
    config.out.write("%d conflicted decisions of %d total:\n"
              % (len(conflicted), len(decisions)))
    for d in decisions:
        pretty_print_merge_decision(base, d, config)


def pretty_print_notebook_merge(bfn, lfn, rfn, bnb, lnb, rnb, mnb, decisions, config=DefaultConfig):
    """Pretty-print a notebook merge

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
    pretty_print_merge_decisions(bnb, decisions, config)
