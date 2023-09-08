// call "nbdime" and compare current version with new version in new tab

define(['base/js/namespace', 'jquery', 'base/js/utils'], function (
  Jupyter,
  $,
  utils,
) {
  'use strict';

  // params are updated on config load
  var params = {
    add_checkpoints_toolbar_button: true,
    add_git_toolbar_button: true,
  };

  // Custom util functions:
  var reStripLeading = /^\/+/;
  var stripLeft = function (string) {
    return string.replace(reStripLeading, '');
  };

  var path_join = function () {
    return stripLeft(utils.url_path_join.apply(this, arguments));
  };

  /**
   * Call nbdime difftool with given base and remote files
   */
  var nbDiffView = function (tool, base, remote) {
    var base_url = Jupyter.notebook.base_url;
    var url =
      window.location.origin +
      '/' +
      path_join(base_url, 'nbdime', tool) +
      '?base=' +
      base;
    if (remote) {
      url += '&remote=' + remote;
    }

    window.open(url);
    $('#doCheckpointDiffView').blur();
  };

  /**
   * Call nbdime difftool with current notebook against checkpointed version
   */
  var nbCheckpointDiffView = function () {
    var nb_dir = utils.url_path_split(Jupyter.notebook.notebook_path)[0];
    var name = Jupyter.notebook.notebook_name;
    var base = path_join(nb_dir, name);

    nbDiffView('checkpoint-difftool', base, '');
  };

  /**
   * Call nbdime difftool with current notebook against checkpointed version
   */
  var nbGitDiffView = function () {
    var nb_dir = utils.url_path_split(Jupyter.notebook.notebook_path)[0];
    var name = Jupyter.notebook.notebook_name;
    var base = path_join(nb_dir, name);

    // Empty file name triggers git, given that it is available on server path
    nbDiffView('git-difftool', base, '');
  };

  var isGit = function (path) {
    var url =
      window.location.origin +
      '/' +
      path_join(Jupyter.notebook.base_url, 'nbdime', 'api', 'isgit');
    var request = {
      data: JSON.stringify({ path: path }),
      method: 'POST',
    };
    return utils.promising_ajax(url, request);
  };

  // The action for checkpoint diffing
  var checkpointAction;

  var setActionEnabledState = function (action, enabled) {
    $("button[data-jupyter-action='" + action + "']").attr(
      'disabled',
      !enabled,
    );
  };

  var setActionTooltip = function (action, tooltip) {
    $("button[data-jupyter-action='" + action + "']").attr('title', tooltip);
  };

  var triggerCheckpointTest = function () {
    Jupyter.notebook.list_checkpoints();
  };

  var onCheckpointsList = function (event, data) {
    // If there are any checkpoints, enable button, if not disable
    setActionEnabledState(checkpointAction, !!data.length);
  };

  var onCheckpointAdded = function (event, data) {
    // Enable button if previously disabled
    setActionEnabledState(checkpointAction, true);
  };

  var register = function (isGit, error) {
    var prefix = 'nbdime';
    var serverMissing = error !== undefined && error.xhr.status === 404;
    var serverMissingMsg =
      'Unable to query nbdime API. Is the server extension enabled?';

    // Register checkpoint action
    checkpointAction = Jupyter.actions.register(
      {
        icon: 'fa-clock-o',
        help: 'Display nbdiff from checkpoint to currently saved version',
        handler: nbCheckpointDiffView,
      },
      'diff-notebook-checkpoint',
      prefix,
    );

    // Register for checkpoint events
    if (!serverMissing) {
      Jupyter.notebook.events.on(
        'checkpoints_listed.Notebook',
        onCheckpointsList,
      );
      Jupyter.notebook.events.on(
        'checkpoint_created.Notebook',
        onCheckpointAdded,
      );
      Jupyter.notebook.events.on(
        'checkpoint_deleted.Notebook',
        triggerCheckpointTest,
      );
    }

    // Check whether to enable button or not
    triggerCheckpointTest();

    if (isGit) {
      // Register git action
      var gitAction = Jupyter.actions.register(
        {
          icon: 'fa-git',
          help: 'Display nbdiff from git HEAD to currently saved version',
          handler: nbGitDiffView,
        },
        'diff-notebook-git',
        prefix,
      );
    }

    if (isGit && params.add_git_toolbar_button) {
      if (params.add_checkpoints_toolbar_button) {
        // Add both buttons, with label on git button
        var btn_group = Jupyter.toolbar.add_buttons_group([
          checkpointAction,
          {
            action: gitAction,
            label: 'nbdiff',
          },
        ]);
      } else {
        // Add only git button, with label on it
        var btn_group = Jupyter.toolbar.add_buttons_group([
          {
            action: gitAction,
            label: 'nbdiff',
          },
        ]);
      }

      // Tooltip for git button:
      if (typeof btn_group !== 'undefined') {
        btn_group
          .children(':last-child')
          .attr('title', Jupyter.actions.get(gitAction).help);
      }
    } else if (params.add_checkpoints_toolbar_button) {
      // Add only checkpoint button, with label on it
      var btn_group = Jupyter.toolbar.add_buttons_group([
        {
          action: checkpointAction,
          label: 'nbdiff',
        },
      ]);
    }

    if (serverMissing) {
      setActionEnabledState(checkpointAction, false);
      console.error(serverMissingMsg);
    }

    // Tooltip for checkpoint button:
    setActionTooltip(
      checkpointAction,
      serverMissing
        ? serverMissingMsg
        : Jupyter.actions.get(checkpointAction).help,
    );
  };

  var load_ipython_extension = function () {
    var promise = isGit(Jupyter.notebook.notebook_path);
    promise.then(
      data => {
        register(data['is_git']);
      },
      error => {
        // Assume that we don't have git
        register(false, error);
      },
    );

    // Update params:
    $.extend(true, params, Jupyter.notebook.config.data.nbdime);
  };

  return {
    load_ipython_extension: load_ipython_extension,
  };
});
