# coding: utf-8

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

import codecs
from collections import defaultdict
import errno
import io
import locale
import os
import re
from subprocess import check_output, CalledProcessError
import sys
from contextlib import contextmanager

import nbformat

if os.name == 'nt':
    EXPLICIT_MISSING_FILE = 'nul'
else:
    EXPLICIT_MISSING_FILE = '/dev/null'


def read_notebook(f, on_null, on_empty=None):
    """Read and return notebook json from filename

    Parameters:
        f:  The filename to read from or null filename
            ("/dev/null" on *nix, "nul" on Windows).
            Alternatively a file-like object can be passed.
        on_null: What to return when filename null
            "empty": return empty dict
            "minimal": return miminal valid notebook
        on_empty: What to return when the file is completely empty (0 size)
            None: Raise an error
            "empty": return empty dict
            "minimal: return minimal valid notebook
    """
    if f == EXPLICIT_MISSING_FILE:
        if on_null == 'empty':
            return {}
        elif on_null == 'minimal':
            return nbformat.v4.new_notebook()
        else:
            raise ValueError(
                'Not valid value for `on_null`: %r. Valid values '
                'are "empty" or "minimal"' % (on_null,))
    else:
        try:
            return nbformat.read(f, as_version=4)
        except nbformat.reader.NotJSONError:
            if on_empty is None:
                raise
            # Reraise if file is not empty
            if isinstance(f, str):
                with io.open(f, encoding='utf-8') as fo:
                    if len(fo.read(10)) != 0:
                        raise
            if on_empty == 'empty':
                return {}
            elif on_empty == 'minimal':
                return nbformat.v4.new_notebook()
            else:
                raise ValueError(
                    'Not valid value for `on_empty`: %r. Valid values '
                    'are None, "empty" or "minimal"' % (on_empty,))


def as_text(text):
    if isinstance(text, list):
        text = "".join(text)
    if isinstance(text, bytes):
        text = text.decode("utf8")
    return text


def as_text_lines(text):
    if isinstance(text, str):
        text = text.splitlines(True)
    if isinstance(text, tuple):
        text = list(text)
    assert isinstance(text, list), 'text argument should be string or string sequence'
    assert all(isinstance(t, str) for t in text), (
        'text argument should be string or string sequence')
    return text


def strings_to_lists(obj):
    if isinstance(obj, dict):
        return {k: strings_to_lists(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [strings_to_lists(v) for v in obj]
    elif isinstance(obj, str):
        return obj.splitlines(True)
    else:
        return obj


def revert_strings_to_lists(obj):
    if isinstance(obj, dict):
        return {k: revert_strings_to_lists(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        if not obj:
            return obj
        elif isinstance(obj[0], str):
            return "".join(obj)
        else:
            return [revert_strings_to_lists(v) for v in obj]
    else:
        return obj


def split_path(path):
    "Split a path on the form '/foo/bar' into ['foo','bar']."
    return [x for x in path.strip("/").split("/") if x]


def join_path(*args):
    "Join a path on the form ['foo','bar'] into '/foo/bar'."
    if len(args) == 1 and isinstance(args[0], (list, tuple, set)):
        args = args[0]
    args = [str(a) for a in args if a not in ["", "/"]]
    ret = "/".join(args)
    return ret if ret.startswith("/") else "/" + ret


r_is_int = re.compile(r"^[-+]?\d+$")

def star_path(path):
    """Replace integers and integer-strings in a path with * """
    path = list(path)
    for i, p in enumerate(path):
        if isinstance(p, int):
            path[i] = '*'
        else:
            if not isinstance(p, str):
                p = p.decode()
            if r_is_int.match(p):
                path[i] = '*'
    return join_path(path)


def resolve_path(obj, path):
    for p in path:
        obj = obj[p]
    return obj


class Strategies(dict):
    """Simple dict wrapper for strategies to allow for wildcard matching of
    list indices + transients collection.
    """
    def __init__(self, *args, **kwargs):
        self.transients = kwargs.pop("transients", [])
        self.fall_back = kwargs.pop("fall_back", None)
        super(Strategies, self).__init__(*args, **kwargs)

    def get(self, k, d=None):
        parts = split_path(k)
        key = star_path(parts)
        return super(Strategies, self).get(key, d)


def is_in_repo(pkg_path):
    """Get whether `pkg_path` is a repository, or is part of one

    Parameters
    ----------
    pkg_path : str
       directory containing package

    Returns
    -------
    is_in_repo : bool
       Whether directory is a part of a repository
    """

    # maybe we are in a repository, check for a .git folder
    p = os.path
    cur_path = None
    par_path = pkg_path
    while cur_path != par_path:
        cur_path = par_path
        if p.exists(p.join(cur_path, '.git')):
            return True
        par_path = p.dirname(par_path)

    return False


def ensure_dir_exists(path):
    """Ensure a directory exists at a given path"""
    if not os.path.exists(path):
        try:
            os.makedirs(path)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise


def locate_gitattributes(scope=None):
    """Locate the .gitattributes file

    returns None if not in a git repo and scope=None
    """
    if scope == 'global':
        try:
            bpath = check_output(['git', 'config', '--global', 'core.attributesfile'])
            gitattributes = os.path.expanduser(bpath.decode('utf8', 'replace').strip())
        except CalledProcessError:
            if os.environ.get('XDG_CONFIG_HOME'):
                gitattributes = os.path.expandvars('$XDG_CONFIG_HOME/git/attributes')
            else:
                gitattributes = os.path.expanduser('~/.config/git/attributes')
    elif scope == 'system':
        # git docs: "Attributes for all users on a system should be placed in
        # the $(prefix)/etc/gitattributes file". Our job is then to check for
        # $(prefix) value.
        try:
            env = os.environ.copy()
            env['GIT_EDITOR'] = 'echo'
            bpath = check_output(['git', 'config', '--system', '-e'], env=env)
            gitconfig = bpath.decode('utf8', 'replace').strip()
            gitattributes = os.path.join(os.path.dirname(gitconfig), 'gitattributes')
        except CalledProcessError:
            # Default to most likely case of empty $(prefix)
            # Sanity check:
            if not os.path.exists('/etc'):
                raise EnvironmentError('Could not find system gitattributes location!')
            gitattributes = os.path.join(['etc', 'gitattributes'])
    else:
        # find .gitattributes in current dir
        path = os.path.abspath('.')
        if not os.path.exists(os.path.join(path, '.git')):
            return None
        gitattributes = os.path.join(path, '.gitattributes')
    return gitattributes


def is_prefix_array(parent, child):
    if parent == child:
        return True
    if not parent:
        return True

    if child is None or len(parent) > len(child):
        return False

    for i in range(len(parent)):
        if parent[i] != child[i]:
            return False
    return True


def find_shared_prefix(a, b):
    if a is None or b is None:
        return None

    if a is b:
        return a[:]

    n = min(len(a), len(b))
    i = 0
    while i < n and a[i] == b[i]:
        i += 1

    return a[:i]


def _setup_std_stream_encoding():
    """Setup encoding on stdout/err

    Ensures sys.stdout/err have error-escaping encoders,
    rather than raising errors.
    """
    if os.getenv('PYTHONIOENCODING'):
        # setting PYTHONIOENCODING overrides anything we would do here
        return
    _default_encoding = locale.getpreferredencoding() or 'UTF-8'
    for name in ('stdout', 'stderr'):
        stream = getattr(sys, name)
        raw_stream = getattr(sys, '__%s__' % name)
        if stream is not raw_stream:
            # don't wrap captured or redirected output
            continue
        enc = getattr(stream, 'encoding', None) or _default_encoding
        errors = getattr(stream, 'errors', None) or 'strict'
        # if error-handler is strict, switch to replace
        if errors == 'strict' or errors.startswith('surrogate'):
            bin_stream = stream.buffer
            new_stream = codecs.getwriter(enc)(bin_stream, errors='backslashreplace')
            setattr(sys, name, new_stream)


def setup_std_streams():
    """Setup sys.stdout/err

    - Ensures sys.stdout/err have error-escaping encoders,
      rather than raising errors.
    - enables colorama for ANSI escapes on Windows
    """

    _setup_std_stream_encoding()
    # must enable colorama after setting up encoding,
    # or encoding will undo colorama setup
    if sys.platform.startswith('win'):
        import colorama
        colorama.init()


def split_os_path(path):
    return os.path.normpath(path).lstrip(os.path.sep).split(os.path.sep)


@contextmanager
def pushd(path):
    """Change current directory with context manager (changes back)"""
    old = os.curdir
    try:
        os.chdir(path)
        yield
    finally:
        os.chdir(old)


class defaultdict2(defaultdict):
    """A defaultdict variant that retains a dictionary of default values.

    When a key in the dictionary is missing, it will first consult the
    default_values instance attribute. If that does not have the key,
    the default_factory will be used as standard defaultdict behavior.
    """

    def __init__(self, default_factory, default_values, *args, **kwargs):
        super(defaultdict2, self).__init__(default_factory, *args, **kwargs)
        self.default_values = default_values

    def copy(self):
        c = super(defaultdict2, self).copy()
        c.default_values = self.default_values.copy()
        return c

    def __missing__(self, key):
        try:
            v = self.default_values[key]
            self[key] = v
            return v
        except KeyError:
            return super(defaultdict2, self).__missing__(key)
