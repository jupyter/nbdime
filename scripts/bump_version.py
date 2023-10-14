# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

import argparse
import shlex
import sys
from pathlib import Path
from subprocess import check_output, run

LERNA_CMD = "npx lerna version --no-push --no-git-tag-version"


def install_dependencies() -> None:
    pkgs = []
    try:
        import hatch
    except ImportError:
        pkgs.append("hatch")
    
    if pkgs:
        run([sys.executable, "-m", "pip", "install"] + pkgs)


def bump(force: bool, spec: str) -> None:
    install_dependencies()

    HERE = Path(__file__).parent.parent.resolve()
    output = check_output(
        shlex.split("git status --porcelain"), cwd=HERE, encoding="utf-8"
    )
    if len(output) > 0:
        print(output)
        # raise Exception("Must be in a clean git state with no untracked files")

    print(f"Executing 'python -m hatch version {spec}'...")
    run(
        [sys.executable, "-m", "hatch", "version", spec], cwd=HERE, encoding="utf-8", check=True
    )

    # convert the Python version
    lerna_cmd = LERNA_CMD
    js_spec = spec
    if spec in ["alpha", "a", "beta", "b", "rc"]:
        js_spec = " --force-publish prerelease"
    elif spec == "release":
        js_spec = " --conventional-commits --no-changelog --conventional-graduate"
    else:
        js_spec += f" --force-publish"

    # bump the JS packages
    if force:
        lerna_cmd += " -y"
    lerna_cmd += f" {js_spec}"
    print(f"Executing '{lerna_cmd}'...")
    run(shlex.split(lerna_cmd), cwd=HERE, check=True, shell=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser("bump_version", "Bump package version")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("spec")

    args = parser.parse_args()
    bump(args.force, args.spec)
