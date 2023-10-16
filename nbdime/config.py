
import os

from jupyter_core.paths import jupyter_config_path

from traitlets import Unicode, Enum, Integer, Bool, HasTraits, Dict, TraitError
from traitlets.config.loader import JSONFileConfigLoader, ConfigFileNotFound

from .merging.notebooks import (
    cli_conflict_strategies, cli_conflict_strategies_input, cli_conflict_strategies_output)




class NbdimeConfigurable(HasTraits):

    def configured_traits(self, cls):
        traits = cls.class_own_traits(config=True)
        c = {}
        for name, _ in traits.items():
            c[name] = getattr(self, name)
        return c


_config_cache = {}
def config_instance(cls):
    if cls in _config_cache:
        return _config_cache[cls]
    instance = _config_cache[cls] = cls()
    return instance


def _load_config_files(basefilename, path=None):
    """Load config files (json) by filename and path.

    yield each config object in turn.
    """

    if not isinstance(path, list):
        path = [path]
    for path in path[::-1]:
        # path list is in descending priority order, so load files backwards:
        loader = JSONFileConfigLoader(basefilename+'.json', path=path)
        config = None
        try:
            config = loader.load_config()
        except ConfigFileNotFound:
            pass
        if config:
            yield config


def recursive_update(target, new, include_none):
    """Recursively update one dictionary using another.

    None values will delete their keys.
    """
    for k, v in new.items():
        if isinstance(v, dict):
            if k not in target:
                target[k] = {}
            recursive_update(target[k], v, include_none)
            if not include_none and not target[k]:
                # Prune empty subdicts
                del target[k]

        elif not include_none and v is None:
            target.pop(k, None)

        else:
            target[k] = v


def build_config(entrypoint, include_none=False):
    if entrypoint not in entrypoint_configurables:
        raise ValueError('Config for entrypoint name %r is not defined! Accepted values are %r.' % (
            entrypoint, list(entrypoint_configurables.keys())
        ))

    # Get config from disk:
    disk_config = {}
    path = jupyter_config_path()
    path.insert(0, os.getcwd())
    for c in _load_config_files('nbdime_config', path=path):
        recursive_update(disk_config, c, include_none)

    config = {}
    configurable = entrypoint_configurables[entrypoint]
    for c in reversed(configurable.mro()):
        if issubclass(c, NbdimeConfigurable):
            recursive_update(config, config_instance(c).configured_traits(c), include_none)
            if (c.__name__ in disk_config):
                recursive_update(config, disk_config[c.__name__], include_none)

    return config


def get_defaults_for_argparse(entrypoint):
    return build_config(entrypoint)


class Global(NbdimeConfigurable):

    log_level = Enum(
        ('DEBUG', 'INFO', 'WARN', 'ERROR', 'CRITICAL'),
        'INFO',
        help="Set the log level by name.",
    ).tag(config=True)


class Web(NbdimeConfigurable):

    port = Integer(
        0,
        help="specify the port you want the server to run on. Default is 0 (random).",
    ).tag(config=True)

    ip = Unicode(
        '127.0.0.1',
        help="specify the interface to listen to for the web server. "
        "NOTE: Setting this to anything other than 127.0.0.1/localhost "
        "might comprimise the security of your computer. Use with care!",
    ).tag(config=True)

    base_url = Unicode(
        '/', help="The base URL prefix under which to run the web app",
    ).tag(config=True)

    browser = Unicode(
        None,
        allow_none=True,
        help="specify the browser to use, to override the system default.",
    ).tag(config=True)

    persist = Bool(
        False, help="prevent server shutting down on remote close request "
                    "(when these would normally be supported).",
    ).tag(config=True)

    workdirectory = Unicode(
        default_value=os.path.abspath(os.path.curdir),
        help="specify the working directory you want "
             "the server to run from. Default is the "
             "actual cwd at program start.",
    ).tag(config=True)


class WebTool(Web):
    pass



class IgnoreConfig(Dict):

    def validate_elements(self, obj, value):
        value = super(IgnoreConfig, self).validate_elements(obj, value)
        for k, v in value.items():
            if not k.startswith('/'):
                raise TraitError('ignore config paths need to start with `/`')
            if not (v in (True, False) or
                    (isinstance(v, (tuple, list, set)) and
                     all(isinstance(i, str) for i in v)
                    )):
                raise TraitError('ignore config value needs to be True, False or a list of strings')
        return self.klass(value)


class _Ignorables(NbdimeConfigurable):

    sources = Bool(
        None,
        allow_none=True,
        help="process/ignore sources.",
    ).tag(config=True)

    outputs = Bool(
        None,
        allow_none=True,
        help="process/ignore outputs.",
    ).tag(config=True)

    metadata = Bool(
        None,
        allow_none=True,
        help="process/ignore metadata.",
    ).tag(config=True)

    id = Bool(
        None,
        allow_none=True,
        help="process/ignore identifiers.",
    ).tag(config=True)

    attachments = Bool(
        None,
        allow_none=True,
        help="process/ignore attachments.",
    ).tag(config=True)

    details = Bool(
        None,
        allow_none=True,
        help="process/ignore details not covered by other options.",
    ).tag(config=True)

    Ignore = IgnoreConfig(
        default_value={},
        help="a custom ignore config"
    ).tag(config=True)


class Show(_Ignorables):
    pass


class _Diffing(_Ignorables):

    color_words = Bool(
        False,
        help=("whether to pass the --color-words flag to any internal calls "
              "to git diff"),
    ).tag(config=True)


class Diff(_Diffing):
    pass


class Merge(_Diffing):

    merge_strategy = Enum(
        cli_conflict_strategies,
        'inline',
        help="Specify the merge strategy to use.",
    ).tag(config=True)

    input_strategy = Enum(
        cli_conflict_strategies_input,
        None,
        allow_none=True,
        help="Specify the merge strategy to use for inputs "
             "(overrides 'merge-strategy' for inputs).",
    ).tag(config=True)

    output_strategy = Enum(
        cli_conflict_strategies_output,
        None,
        allow_none=True,
        help="Specify the merge strategy to use for outputs "
             "(overrides 'merge-strategy' for outputs).",
    ).tag(config=True)

    ignore_transients = Bool(
        True,
        help="Disallow deletion of transient data such as outputs and "
             "execution counts in order to resolve conflicts.",
    ).tag(config=True)


class GitDiff(Diff):
    use_filter = Bool(
        False,
        help="if enabled, will apply any configured git filter to the remote file "
             "prior to diffing."
    )

class GitMerge(Merge):
    pass


class NbDiff(GitDiff):
    pass

class NbDiffWeb(Web, GitDiff):
    pass

class NbMerge(Merge):
    pass

class NbMergeWeb(Web, Merge):

    show_base = Bool(
        True,
        help="Whether to show the base version (4-panels) or not (3-panels).",
    ).tag(config=True)

class NbShow(Show):
    pass

class Server(Web):

    port = Integer(
        8888,
        help="specify the port you want the server to run on. Default is 8888.",
    ).tag(config=True)


class NbDiffDriver(GitDiff):
    pass

class NbDiffTool(GitDiff, WebTool):
    pass

class NbMergeDriver(GitMerge):
    pass

class NbMergeTool(GitMerge, WebTool):
    pass

class Extension(GitDiff):
    pass


entrypoint_configurables = {
    'nbdiff': NbDiff,
    'nbdiff-web': NbDiffWeb,
    'nbmerge': NbMerge,
    'nbmerge-web': NbMergeWeb,
    'nbshow': NbShow,
    'server': Server,
    'extension': Extension,
    'git-nbdiffdriver': NbDiffDriver,
    'git-nbdifftool': NbDiffTool,
    'git-nbmergedriver': NbMergeDriver,
    'git-nbmergetool': NbMergeTool,
}


class Namespace(object):
    def __init__(self, adict):
        self.__dict__.update(adict)
