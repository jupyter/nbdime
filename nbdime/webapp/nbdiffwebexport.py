import sys
import os
import json

from jinja2 import FileSystemLoader, Environment

from ..args import (
    Path,
    ConfigBackedParser,
    add_generic_args)

from ..nbdiffapp import (
    list_changed_file_pairs,
    resolve_diff_args,
    _build_diff)


here = os.path.abspath(os.path.dirname(__file__))
static_path = os.path.join(here, 'static')
template_path = os.path.join(here, 'templates')


def build_arg_parser():
    """
    Creates an argument parser for the diff tool, that also lets the
    user specify a port and displays a help message.
    """
    description = 'Difftool for Nbdime.'
    parser = ConfigBackedParser(
        description=description,
        add_help=True
        )
    add_generic_args(parser)
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
        "paths", help="filter diffs for git-revisions based on path",
        type=Path,
        nargs='*', default=None,
    )
    parser.add_argument(
        "--nbdime_url",
        type=Path,
        default="",
        help="URL to nbdime.js. If missing output html will contain the script embedded"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default="output/",
        help="a path to an output dir"
    )
    return parser


def main_export(opts):
    env = Environment(loader=FileSystemLoader([template_path]), autoescape=False)
    outputdir = opts.output_dir
    nbdime_content = ""
    nbdime_url = opts.nbdime_url
    if not nbdime_url:
        # if nbdime_url is empty then we would embed the script
        with open(os.path.join(static_path, "nbdime.js"), "r") as f:
            nbdime_content = f.read()

    base, remote, paths = resolve_diff_args(opts)
    index = 1
    for fbase, fremote in list_changed_file_pairs(base, remote, paths):
        # on_null="minimal" is crucial cause web renderer expects
        # base_notebook to be a valid notebook even if it is missing
        try:
            base_notebook, remote_notebook, diff = _build_diff(fbase, fremote, on_null="minimal")
        except ValueError as e:
            print(e, file=sys.stderr)
            return 1
        data = json.dumps(dict(
            base=base_notebook,
            diff=diff
        ))

        template = env.get_template("diffembedded.html")
        rendered = template.render(
            data=data,
            nbdime_url=nbdime_url,
            nbdime_content=nbdime_content)
        outputfilename = os.path.join(outputdir, "diff" + str(index) + ".html")
        with open(outputfilename, "w") as f:
            f.write(rendered)
        index += 1
    return 0


def main(args=None):
    if args is None:
        args = sys.argv[1:]
    opts = build_arg_parser().parse_args(args)
    return main_export(opts)


if __name__ == "__main__":
    sys.exit(main())
