# coding: utf-8

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import unicode_literals

from six import string_types, text_type

import re
import os


def as_text(text):
    if isinstance(text, list):
        text = "".join(text)
    if isinstance(text, bytes):
        text = text.decode("utf8")
    return text


def as_text_lines(text):
    if isinstance(text, string_types):
        text = text.splitlines(True)
    if isinstance(text, tuple):
        text = list(text)
    assert isinstance(text, list)
    assert all(isinstance(t, string_types) for t in text)
    return text


def strings_to_lists(obj):
    if isinstance(obj, dict):
        return {k: strings_to_lists(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [strings_to_lists(v) for v in obj]
    elif isinstance(obj, string_types):
        return obj.splitlines(True)
    else:
        return obj


def revert_strings_to_lists(obj):
    if isinstance(obj, dict):
        return {k: revert_strings_to_lists(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        if not obj:
            return obj
        elif isinstance(obj[0], string_types):
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
            if not isinstance(p, text_type):
                p = p.decode()
            if r_is_int.match(p):
                path[i] = '*'
    return join_path(path)


class Strategies(dict):
    """Simple dict wrapper for strategies to allow for wildcard matching of
    list indices + transients collection.
    """
    def __init__(self, *args, **kwargs):
        self.transients = kwargs.get("transients", [])
        self.fall_back = kwargs.get("fall_back", None)
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
