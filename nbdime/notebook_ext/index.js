// call "nbdime" and compare current version with new version in new tab

define([
    'base/js/namespace',
    'jquery',
    'base/js/utils'
], function(Jupyter, $, utils) {
    "use strict";

    // Custom util functions:
    var reStripLeading = /^\/+/
    var stripLeft = function (string) {
        return string.replace(reStripLeading, '');
    };

    var path_join = function () {
        return stripLeft(utils.url_path_join.apply(this, arguments));
    }

    /**
     * Call nbdime difftool with given base and remote files
     */
    var nbDiffView = function (tool, base, remote) {
        var base_url = Jupyter.notebook.base_url;
        var url = window.location.origin + '/' + path_join(base_url, 'nbdime', tool) +
            '?base=' + base;
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
        var base = path_join(nb_dir, '.ipynb_checkpoints', utils.splitext(name)[0] + '-checkpoint.ipynb');
        var remote = path_join(nb_dir, name);

        nbDiffView('difftool', base, remote);
    };


    var load_ipython_extension = function() {
        var prefix = 'nbdime';

        var checkpointAction = Jupyter.actions.register({
            icon: 'fa-clock-o',
            help: 'Display nbdiff from checkpoint to currently saved version',
            handler : nbCheckpointDiffView
        }, 'diff-notebook-checkpoint', prefix);

        var btn_group = Jupyter.toolbar.add_buttons_group([{
            action: checkpointAction,
            label: 'nbdiff',
        }]);

        btn_group.children(':first-child').attr('title', Jupyter.actions.get(checkpointAction).help);
    };

    return {
        load_ipython_extension : load_ipython_extension
    };
});
