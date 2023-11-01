# coding: utf-8

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.




from contextlib import contextmanager
import os
import requests
import shlex
import sys
import time
from subprocess import check_output, check_call, STDOUT, CalledProcessError

import pytest
import nbformat

from nbdime import patch, diff
from nbdime.diff_format import is_valid_diff


from shutil import which

pjoin = os.path.join

have_git = which('git')
have_hg = which('hg')

WEB_TEST_TIMEOUT = 15

TEST_TOKEN = 'nbdime-test-token'


def assert_is_valid_notebook(nb):
    """These are the current assumptions on notebooks in these tests. Loosen on demand."""
    assert nb["nbformat"] == 4
    # assert nb["nbformat_minor"] == 0
    assert isinstance(nb["metadata"], dict)
    assert isinstance(nb["cells"], list)
    assert all(isinstance(cell, dict) for cell in nb["cells"])


def check_diff_and_patch(a, b):
    "Check that patch(a, diff(a,b)) reproduces b."
    d = diff(a, b)
    assert is_valid_diff(d)
    assert patch(a, d) == b


def check_symmetric_diff_and_patch(a, b):
    "Check that patch(a, diff(a,b)) reproduces b and vice versa."
    check_diff_and_patch(a, b)
    check_diff_and_patch(b, a)


def sources_to_notebook(sources, cell_type='code', id_seed=0, strip_ids=False):
    assert isinstance(sources, list)
    nb = nbformat.v4.new_notebook()
    for source in sources:
        if isinstance(source, list):
            source = "".join(source)
        if cell_type == 'code':
            nb.cells.append(nbformat.v4.new_code_cell(source))
        elif cell_type == 'markdown':
            nb.cells.append(nbformat.v4.new_markdown_cell(source))
    if strip_ids:
        strip_cell_ids(nb)
    else:
        deterministic_cell_ids(nb)
    return nb


def notebook_to_sources(nb, as_str=True):
    sources = []
    for cell in nb["cells"]:
        source = cell["source"]
        if as_str and isinstance(source, list):
            source = "\n".join([line.strip("\n") for line in source])
        elif not as_str and isinstance(source, str):
            source = source.splitlines(True)
        sources.append(source)
    return sources


def outputs_to_notebook(outputs, strip_ids=False):
    assert isinstance(outputs, list)
    assert len(outputs) == 0 or isinstance(outputs[0], list)
    nb = nbformat.v4.new_notebook()
    for cell_outputs in outputs:
        cell = nbformat.v4.new_code_cell()
        nb.cells.append(cell)
        for output in cell_outputs:
            if isinstance(output, str):
                output = nbformat.v4.new_output(
                    output_type="display_data",
                    data={
                        "text/plain": output,
                    }
                )
            assert isinstance(output, dict)
            cell.outputs.append(output)
    if strip_ids:
        strip_cell_ids(nb)
    else:
        deterministic_cell_ids(nb)
    return nb


def strip_cell_id(cell):
    if "id" in cell:
        del cell["id"]
    return cell


def strip_cell_ids(nb):
    for cell in nb["cells"]:
        strip_cell_id(cell)
    return nb


def deterministic_cell_ids(nb):
    for i, cell in enumerate(nb["cells"]):
        cell["id"] = f"cell-id-{i}"
    return nb

def new_cell_wo_id(*args, **kwargs):
    cell = nbformat.v4.new_code_cell(*args, **kwargs)
    strip_cell_id(cell)
    return cell


@contextmanager
def assert_clean_exit():
    """Assert that SystemExit is called with code=0"""
    with pytest.raises(SystemExit) as e:
        yield
    assert e.value.code == 0


def call(cmd):
    """Call a command

    if str, split into command list
    """
    if isinstance(cmd, str):
        cmd = shlex.split(cmd)
    return check_call(cmd, stdout=sys.stdout, stderr=sys.stderr)


def get_output(cmd, err=False, returncode=0):
    """Run a command and get its output (as text)"""
    if isinstance(cmd, str):
        cmd = shlex.split(cmd)
    stderr = STDOUT if err else sys.stderr
    try:
        output = check_output(cmd, stderr=stderr).decode('utf8', 'replace')
    except CalledProcessError as e:
        if e.returncode != returncode:
            raise
        return e.output.decode('utf8', 'replace')
    else:
        if returncode != 0:
            raise CalledProcessError(0, cmd, output.encode('utf8'), stderr)
    return output


def wait_up(url, interval=0.1, check=None):
    while True:
        try:
            r = requests.get(url)
        except Exception:
            if check:
                assert check()
            print("waiting for %s" % url)
            time.sleep(interval)
        else:
            break



MERCURIAL_TEST_CONFIG = """
[extensions]
extdiff =

[extdiff]
cmd.nbdiff = hg-nbdiff
cmd.nbdiffweb = hg-nbdiffweb
opts.nbdiffweb = --log-level DEBUG --browser=disabled

[merge-tools]
nbdime.priority = 2
nbdime.premerge = False
nbdime.executable = hg-nbmerge
nbdime.args = $base $local $other $output
nbdimeweb.priority = 1
nbdimeweb.premerge = False
nbdimeweb.executable = hg-nbmergeweb
nbdimeweb.args = --log-level DEBUG --browser=disabled $base $local $other $output
nbdimeweb.gui = True

[merge-patterns]
**.ipynb = nbdime
"""


def write_local_hg_config(repo_path):
    fn = pjoin(repo_path, ".hg", "hgrc")
    with open(fn, 'w') as f:
        f.write(MERCURIAL_TEST_CONFIG)
