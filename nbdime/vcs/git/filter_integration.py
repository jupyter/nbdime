
import io
from subprocess import check_output, STDOUT, CalledProcessError

from io import StringIO

from nbdime.utils import EXPLICIT_MISSING_FILE


class NamedStringIO(StringIO):
    name = ''


def interrogate_filter(path):
    """Check whether a filter git attribute is set for path.

    Returns None if no valid filter attribute could be found.
    """
    # Ask for the filter attributes of file on path (-z = null-terminated fields)
    try:
        spec = check_output(['git', 'check-attr', '-z', 'filter', path])
    except CalledProcessError:
        return None
    try:
        path_list, attr, info = [s.decode('utf8', 'replace') for s in spec.split(b'\x00')[:3]]
    except ValueError:
        # For older versions of git, the `-z` flag is unsupported
        # This will then raise a ValueError when trying to unpack
        return None
    if attr != 'filter' or path != path_list:
        raise ValueError(
            'Unexpected output from git check-attr. ' +
            ('Expected to start with "%s\x00filter", ' % path) +
            ('started with "%s\x00%s"' % (path_list, attr))
        )
    if not info or info in ('unspecified', 'set', 'unset'):
        return None
    # We have a valid attribute
    return info


def get_clean_filter_cmd(filter_attr):
    """Given a filter attribute, look up its driver in git config.

    Returns None if noe valid config could be found.
    """
    try:
        spec = check_output([
            'git', 'config', '--get', '-z', 'filter.%s.clean' % filter_attr
        ])
        return spec.split(b'\x00')[0].decode('utf8', 'replace') or None
    except CalledProcessError:
        return None


def apply_possible_filter(git_path, path=None):
    """Apply any configured git filters to path.

    Returns the original remote path if no filter is configured,
    or a StringIO instance with the filtered content if a filter
    should be applied.
    """
    if path is None:
        path = git_path

    if path == EXPLICIT_MISSING_FILE:
        return path

    filter_attr = interrogate_filter(git_path)
    if not filter_attr:
        return path
    filter_cmd = get_clean_filter_cmd(filter_attr)
    if not filter_cmd:
        return path

    # Apply filter and pipe to a string buffer
    with io.open(path, 'r', encoding="utf8") as f:
        output = check_output(
            filter_cmd,
            stdin=f,
            stderr=STDOUT, shell=True
        ).decode('utf8', 'replace')
    buffer = NamedStringIO()
    buffer.name = path
    buffer.write(output)
    buffer.seek(0)
    return buffer
