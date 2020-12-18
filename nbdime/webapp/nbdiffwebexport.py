import sys
import os
import json

from jinja2 import FileSystemLoader, Environment

from ..args import (
    Path,
    ConfigBackedParser,
    add_generic_args,
    add_diff_args)

from ..nbdiffapp import (
    list_changed_file_pairs,
    resolve_diff_args,
    _build_diff)


here = os.path.abspath(os.path.dirname(__file__))
static_path = os.path.join(here, 'static')
template_path = os.path.join(here, 'templates')


def build_arg_parser():
    """
    Creates an argument parser for the web diff exporter.
    """
    description = 'Export Nbdime diff.'
    parser = ConfigBackedParser(
        description=description,
        add_help=True
        )
    add_generic_args(parser)
    add_diff_args(parser)
    parser.add_argument(
        "base", help="the base notebook filename OR base git-revision.",
        type=Path,
        nargs='?', default='HEAD',
    )
    parser.add_argument(
        "remote", help="the remote modified notebook filename OR remote git-revision.",
        type=Path,
        nargs='?', default=None,
    )
    parser.add_argument(
        "paths", help="filter diffs for git-revisions based on path.",
        type=Path,
        nargs='*', default=None,
    )
    parser.add_argument(
        "--nbdime-url",
        default="",
        help="URL to nbdime.js. If missing the script will be embedded in the HTML page."
    )
    parser.add_argument(
        "--mathjax-url",
        default="",
        help="URL to MathJax JS. If blank, typsetting of LaTeX won't be available in the diff view."
    )
    parser.add_argument(
        "--mathjax-config",
        default="TeX-AMS_HTML-full,Safe",
        help="config string for MathJax."
    )
    parser.add_argument(
        '--show-unchanged',
        dest='hide_unchanged',
        action="store_false",
        default=True,
        help="show unchanged cells by default"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=".",
        help="path to output directory."
    )
    return parser


def main_export(opts):

    outputdir = opts.output_dir
    os.makedirs(outputdir, exist_ok=True)

    nbdime_content = ""
    nbdime_url = opts.nbdime_url
    if not nbdime_url:
        # if nbdime_url is empty then we would embed the script
        with open(os.path.join(static_path, "nbdime.js"), "r", encoding='utf8') as f:
            nbdime_content = f.read()

    base, remote, paths = resolve_diff_args(opts)

    env = Environment(loader=FileSystemLoader([template_path]), autoescape=False)
    index = 1
    for fbase, fremote in list_changed_file_pairs(base, remote, paths):
        # on_null="minimal" is crucial cause web renderer expects
        # base_notebook to be a valid notebook even if it is missing
        try:
            base_notebook, remote_notebook, diff = _build_diff(fbase, fremote, on_null="minimal")
        except ValueError as e:
            print(e, file=sys.stderr)
            return 1
        data = dict(
            base=base_notebook,
            diff=diff
        )

        config = dict(
            hideUnchange=opts.hide_unchanged,
            mathjaxUrl=opts.mathjax_url,
            mathjaxConfig=opts.mathjax_config,
        )

        # TODO: Create labels for use in template + filenames (instead of index)
        template = env.get_template("diffembedded.html")
        rendered = template.render(
            data=data,
            nbdime_js_url=nbdime_url,
            nbdime_js_content=nbdime_content,
            base_label='Base',
            remote_label='Remote',
            config_data=config,
        )
        outputfilename = os.path.join(outputdir, "nbdiff-" + str(index) + ".html")
        with open(outputfilename, "w", encoding="utf8") as f:
            f.write(rendered)
        index += 1
    print('Wrote %d diffs to %s' % (index - 1, outputdir))
    return 0


def main(args=None):
    if args is None:
        args = sys.argv[1:]
    opts = build_arg_parser().parse_args(args)
    return main_export(opts)


if __name__ == "__main__":
    sys.exit(main())
