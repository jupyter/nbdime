#!/usr/bin/env python
# -*- coding:utf-8 -*-



import json
import os

from jinja2 import ChoiceLoader, FileSystemLoader

from jupyter_server.utils import url_path_join, to_os_path, ensure_async

generic_checkpoint_mixin_types = []
file_checkpoint_mixin_types = []

try:
    from jupyter_server.services.contents.checkpoints import GenericCheckpointsMixin as jpserver_GenericCheckpointsMixin
    from jupyter_server.services.contents.filecheckpoints import FileCheckpoints as jpserver_FileCheckpoints
    generic_checkpoint_mixin_types.append(jpserver_GenericCheckpointsMixin)
    file_checkpoint_mixin_types.append(jpserver_FileCheckpoints)
except ModuleNotFoundError:
    pass

try:
    from notebook.services.contents.checkpoints import GenericCheckpointsMixin as nbserver_GenericCheckpointsMixin
    from notebook.services.contents.filecheckpoints import FileCheckpoints as nbserver_FileCheckpoints
    generic_checkpoint_mixin_types.append(nbserver_GenericCheckpointsMixin)
    file_checkpoint_mixin_types.append(nbserver_FileCheckpoints)
except ModuleNotFoundError:
    pass

generic_checkpoint_mixin_types = tuple(generic_checkpoint_mixin_types)
file_checkpoint_mixin_types = tuple(file_checkpoint_mixin_types)


from tornado.web import HTTPError, escape, authenticated, gen

from ..args import process_diff_flags
from ..config import build_config, Namespace
from ..diffing.notebooks import set_notebook_diff_ignores, diff_notebooks
from ..gitfiles import (
    changed_notebooks, is_path_in_repo, find_repo_root,
    InvalidGitRepositoryError, BadName, GitCommandNotFound,
    GitRefWorkingTree, GitRefIndex
    )
from ..ignorables import diff_ignorables
from ..utils import read_notebook

from .nbdimeserver import (
    template_path,
    static_path,
    NbdimeHandler,
    MainDifftoolHandler,
    ApiDiffHandler,
    APIHandler,
)


special_refs = {
    'working': GitRefWorkingTree,
    'index': GitRefIndex,
}


class AuthMainDifftoolHandler(MainDifftoolHandler):
    @authenticated
    def get(self):
        return super(AuthMainDifftoolHandler, self).get()


class GitDifftoolHandler(NbdimeHandler):
    """Diff tool handler that also handles showing diff to git HEAD"""

    @authenticated
    def get(self):
        args = self.base_args()
        args['base'] = 'git:' + self.get_argument('base', '')
        args['remote'] = ''

        self.write(self.render_template(
            'difftool.html',
            config_data=args,
            ))


class CheckpointDifftoolHandler(NbdimeHandler):
    """Diff tool handler that also handles showing diff to git HEAD"""

    @authenticated
    def get(self):
        args = self.base_args()
        args['base'] = 'checkpoint:' + self.get_argument('base', '')
        args['remote'] = ''

        self.write(self.render_template(
            'difftool.html',
            config_data=args,
            ))


class BaseGitDiffHandler(ApiDiffHandler):

    def get_git_notebooks(self, file_path_arg, ref_base='HEAD', ref_remote=None):
        """
        Gets the content of the before and after state of the notebook based on the given Git refs.

        :param file_path_arg: The path to the file being diffed
        :param ref_base: the Git ref for the "local" or the "previous" state
        :param ref_remote: the Git ref for the "remote" or the "current" state
        :return: (base_nb, remote_nb)
        """
        # Sometimes the root dir of the files is not cwd
        nb_root = getattr(self.contents_manager, 'root_dir', None)
        # Resolve base argument to a file system path
        file_path = os.path.realpath(to_os_path(file_path_arg, nb_root))

        # Ensure path/root_dir that can be sent to git:
        try:
            git_root = find_repo_root(file_path)
        except InvalidGitRepositoryError as e:
            self.log.exception(e)
            raise HTTPError(422, 'Invalid notebook: %s' % file_path)
        file_path = os.path.relpath(file_path, git_root)

        # Get the base/remote notebooks:
        try:
            for fbase, fremote in changed_notebooks(ref_base, ref_remote, file_path, git_root):
                base_nb = read_notebook(fbase, on_null='minimal')
                remote_nb = read_notebook(fremote, on_null='minimal')
                break  # there should only ever be one set of files
            else:
                # The filename was either invalid or the file is unchanged
                # Assume unchanged, and let read_notebook handle error
                # reporting if invalid
                base_nb = self.read_notebook(os.path.join(git_root, file_path))
                remote_nb = base_nb
        except (InvalidGitRepositoryError, BadName) as e:
            self.log.exception(e)
            raise HTTPError(422, 'Invalid notebook: %s' % file_path_arg)
        except GitCommandNotFound as e:
            self.log.exception(e)
            raise HTTPError(
                500, 'Could not find git executable. '
                     'Please ensure git is available to the server process.')

        return base_nb, remote_nb

    @property
    def curdir(self):
        root_dir = getattr(self.contents_manager, 'root_dir', None)
        if root_dir is None:
            return super(ExtensionApiDiffHandler, self).curdir
        return root_dir


class ExtensionApiDiffHandler(BaseGitDiffHandler):
    """Diff API handler that also handles diff to git HEAD"""

    async def _get_checkpoint_notebooks(self, base):
        # Get the model for the current notebook:
        cm = self.contents_manager
        model = await ensure_async(cm.get(base, content=True, type='notebook'))
        remote_nb = model['content']
        # Get the model for the checkpoint notebook:
        checkpoints = await ensure_async(cm.list_checkpoints(base))
        if not checkpoints:
            # No checkpoints, indicate unchanged:
            self.log.info('No checkpoints for file: %r, %r', base, checkpoints)
            return remote_nb, remote_nb
        self.log.debug('Checkpoints: %r', checkpoints)
        checkpoint = checkpoints[0]
        if isinstance(cm.checkpoints, generic_checkpoint_mixin_types):
            checkpoint_model = await ensure_async(
                cm.checkpoints.get_notebook_checkpoint(checkpoint, base))
            base_nb = checkpoint_model['content']
        elif isinstance(cm.checkpoints, file_checkpoint_mixin_types):
            path = await ensure_async(
                cm.checkpoints.checkpoint_path(checkpoint['id'], base))
            base_nb = read_notebook(path, on_null='minimal')
        else:
            raise RuntimeError('Unknown checkpoint handler interface')
        return base_nb, remote_nb

    @authenticated
    async def post(self):
        # TODO: Add deprecation warning (for git/checkpoint only?)
        # Assuming a request on the form "{'argname':arg}"
        body = json.loads(escape.to_unicode(self.request.body))
        base = body['base']
        if base.startswith('git:'):
            base_nb, remote_nb = self.get_git_notebooks(base[len('git:'):])
        elif base.startswith('checkpoint:'):
            base_nb, remote_nb = await self._get_checkpoint_notebooks(base[len('checkpoint:'):])
        else:
            # Regular files, call super
            super(ExtensionApiDiffHandler, self).post()
            return

        # Perform actual diff and return data:
        try:
            thediff = diff_notebooks(base_nb, remote_nb)
        except Exception:
            self.log.exception('Error diffing documents:')
            raise HTTPError(500, 'Error while attempting to diff documents')

        data = {
            'base': base_nb,
            'diff': thediff,
            }
        self.finish(data)


class GitDiffHandler(BaseGitDiffHandler):
    """Diff API handler that handles diffs for two git refs"""

    @classmethod
    def parse_ref(cls, data):
        return data.get('git', None) or special_refs[data['special'].lower()]

    def _validate_request(self, body):
        def _fail(msg):
            self.log.exception(msg)
            raise HTTPError(400, msg)

        # Validate refs
        for refname in ('ref_local', 'ref_remote'):

            # Validate ref_curr
            try:
                ref = body[refname]
            except KeyError:
                _fail('Required key %s not provided in the request' % (refname))

            # Either of special or git is supported in ref
            if 'special' in ref and 'git' in ref:
                _fail('Only one of special and git should be present in git '
                      'reference.')

            if not ('special' in ref or 'git' in ref):
                _fail('At least one of special and git should be present in git '
                      'reference.')

            if 'special' in ref:
                special = ref['special'].lower()
                if refname == 'ref_local':
                    if special != 'index':
                        _fail('Only "index" is allowed for the "special" value '
                              'on ref_local, got %r.' % (special,))
                elif special not in ('index', 'working'):
                    _fail('Only "index" or "working" is allowed for the "special" value '
                          'on ref_remote, got %r.' % (special,))


        # Validate file_name
        try:
            body['file_path']
        except KeyError:
            _fail('Required value file_path not provided in the request')


    @authenticated
    @gen.coroutine
    def post(self):
        body = json.loads(escape.to_unicode(self.request.body))

        try:
            # Validate the request input
            self._validate_request(body)

            # Get file contents based on Git regs
            ref_local = body['ref_local']
            ref_remote = body['ref_remote']
            file_path = body['file_path']
            base_nb, remote_nb = self.get_git_notebooks(
                file_path,
                GitDiffHandler.parse_ref(ref_local),
                GitDiffHandler.parse_ref(ref_remote),
            )

            # Perform actual diff and return data
            thediff = diff_notebooks(base_nb, remote_nb)

            data = {
                'base': base_nb,
                'diff': thediff,
            }
            self.finish(data)
        except HTTPError:
            raise
        except Exception:
            self.log.exception('Error diffing documents:')
            raise HTTPError(500, 'Error while attempting to diff documents')


class IsGitHandler(NbdimeHandler, APIHandler):
    """API handler for querying if path is in git repo"""

    @authenticated
    def post(self):
        root_dir = getattr(self.contents_manager, 'root_dir', None)
        # Ensure notebooks are file-system based
        if root_dir is None:
            self.finish({'is_git': False})

        # Assuming a request on the form "{'argname':arg}"
        body = json.loads(escape.to_unicode(self.request.body))
        nb = os.path.join(root_dir, body['path'])

        data = {'is_git': is_path_in_repo(nb)}
        self.finish(data)


def _load_jupyter_server_extension(nb_server_app, nb6_entrypoint=False):
    """
    Called when the extension is loaded.

    Args:
        nb_server_app (NotebookWebApplication): handle to the Notebook webserver instance.
    """
    if nb6_entrypoint:
        # We're using the old notebook 6 extenstion entry point
        # In this case, we only support jupyter_server < 2, so fail if >=2
        from jupyter_server._version import __version__
        try:
            from packaging.version import parse, Version
            if parse(__version__) >= Version('2.0.0'):
                nb_server_app.log.critical(
                    "You must use Jupyter Server v1 to load nbdime as a classic notebook server extension. "
                    f"You have v{__version__} installed.\nYou can fix this by executing:\n"
                    "    pip install -U \"jupyter-server<2.0.0\""
                )
                return
        except Exception: # noqa
            pass
    web_app = nb_server_app.web_app

    env = web_app.settings['jinja2_env']

    env.loader = ChoiceLoader([
        env.loader,
        FileSystemLoader(template_path),
    ])

    config = build_config('extension')
    ignore = config.pop('Ignore', None)
    for k in diff_ignorables:
        config[k] = config.get(k, None)
    ns = Namespace(config)
    process_diff_flags(ns)
    if ignore:
        set_notebook_diff_ignores(ignore)

    web_app.settings['static_path'].append(static_path)

    params = {
        'nbdime_relative_base_url': 'nbdime',
        'closable': False,
    }
    handlers = [
        (r'/nbdime/difftool', AuthMainDifftoolHandler, params),
        (r'/nbdime/checkpoint-difftool', CheckpointDifftoolHandler, params),
        (r'/nbdime/git-difftool', GitDifftoolHandler, params),
        (r'/nbdime/api/diff', ExtensionApiDiffHandler, params),
        (r'/nbdime/api/isgit', IsGitHandler, params),
        (r'/nbdime/api/gitdiff', GitDiffHandler, params)
    ]

    # Prefix routes with base_url:
    base_url = web_app.settings.get('base_url', '/')
    handlers = [(url_path_join(base_url, h[0]), h[1], h[2]) for h in handlers]

    host_pattern = '.*$'
    web_app.add_handlers(host_pattern, handlers)
