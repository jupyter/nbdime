
import os
import shutil
import tempfile

from nbdime.utils import strings_to_lists, revert_strings_to_lists, is_in_repo

def test_string_to_lists():
    obj = {"c": [{"s": "ting\ntang", "o": [{"ot": "stream"}]}]}
    obj2 = strings_to_lists(obj)
    obj3 = revert_strings_to_lists(obj2)
    assert obj3 == obj

def test_is_repo():
    try:
        tmpdir = tempfile.mkdtemp(prefix='nbdime-test')
        subdir = tempfile.mkdtemp(dir=tmpdir)
        subfile = tempfile.NamedTemporaryFile(dir=tmpdir)
        subsubfile = tempfile.NamedTemporaryFile(dir=subdir)
        with subfile, subsubfile:
            assert False == is_in_repo(tmpdir)
            assert False == is_in_repo(subdir)
            assert False == is_in_repo(subfile.name)
            assert False == is_in_repo(subsubfile.name)
            os.makedirs(os.path.join(subdir, '.git'))
            assert False == is_in_repo(tmpdir)
            assert True == is_in_repo(subdir)
            assert False == is_in_repo(subfile.name)
            assert True == is_in_repo(subsubfile.name)
            os.makedirs(os.path.join(tmpdir, '.git'))
            assert True == is_in_repo(tmpdir)
            assert True == is_in_repo(subdir)
            assert True == is_in_repo(subfile.name)
            assert True == is_in_repo(subsubfile.name)

    finally:
        shutil.rmtree(tmpdir)
