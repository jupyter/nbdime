# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

import argparse
import shlex
import sys
from pathlib import Path
from subprocess import check_output, check_call

from packaging.version import parse

try:
    from jupyter_releaser import run
except ImportError:
    def run(cmd, **kwargs):
        check_call(shlex.split(cmd), encoding="utf-8", **kwargs)


def get_current_version() -> str:
    """Get the current version using hatch."""
    return check_output(
        shlex.split(f"{sys.executable} -m hatch version"),
        encoding="utf-8"
    ).strip()


def resolve_next_spec(version: str) -> str:
    """Resolve 'next' spec to concrete version spec.

    For pre-releases (dev, alpha, beta, rc), bumps the pre-release number.
    For final releases, bumps the patch version.
    """
    v = parse(version)

    if v.is_devrelease:
        return "dev"

    if v.is_prerelease and v.pre is not None:
        pre_type = v.pre[0]
        return {"a": "alpha", "b": "beta", "rc": "rc"}[pre_type]

    return "patch"


LERNA_CMD = "npx lerna version --no-push --no-git-tag-version"


def install_dependencies() -> None:
    pkgs = []
    try:
        import hatch
    except ImportError:
        pkgs.append("hatch")
    
    if pkgs:
        run(f"{sys.executable} -m pip install {' '.join(pkgs)}")


def bump(force: bool, spec: str) -> None:
    install_dependencies()

    HERE = Path(__file__).parent.parent.resolve()
    output = check_output(
        shlex.split("git status --porcelain"), cwd=HERE, encoding="utf-8"
    )
    if len(output) > 0:
        print(output)
        raise Exception("Must be in a clean git state with no untracked files")

    # Handle 'next' spec by resolving to appropriate version bump
    if spec == "next":
        current_version = get_current_version()
        spec = resolve_next_spec(current_version)
        print(f"Resolved 'next' to '{spec}' (current version: {current_version})")

    print(f"Executing 'python -m hatch version {spec}'...")
    run(
        f"{sys.executable} -m hatch version {spec}", cwd=HERE
    )

    # convert the Python version
    lerna_cmd = LERNA_CMD
    if spec in ["alpha", "a", "beta", "b", "rc", "dev"]:
        js_spec = "--force-publish"
        spec = "prerelease"
    elif spec == "release":
        js_spec = "--conventional-commits --no-changelog --conventional-graduate"
        spec = ""
    else:
        js_spec = f"--force-publish"

    # bump the JS packages
    if force:
        # This needs to be the latest option for weird reason
        js_spec += " -y"
    lerna_cmd += f" {js_spec} {spec}"
    print(f"Executing '{lerna_cmd}'...")
    run(lerna_cmd, cwd=HERE)

    print(f"Changed made:")
    run("git diff", cwd=HERE)


if __name__ == "__main__":
    parser = argparse.ArgumentParser("bump_version", "Bump package version")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("spec")

    args = parser.parse_args()
    bump(args.force, args.spec)
