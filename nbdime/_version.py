# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

import re
from collections import namedtuple

VersionInfo = namedtuple("VersionInfo", ["major", "minor", "micro", "releaselevel", "serial"])

_specifier_ = {"a": "alpha", "b": "beta", "rc": "candidate", "": "final"}

__version__ = "4.0.0a1"

parser = re.compile(r"^(?P<major>\d+)\.(?P<minor>\d+)\.(?P<micro>\d+)((?P<releaselevel>a|b|rc)(?P<serial>\d+))?$")

parsed_version = parser.match(__version__)
groups = parsed_version.groupdict()
version_info = VersionInfo(
    int(groups["major"]),
    int(groups["minor"]),
    int(groups["micro"]),
    _specifier_[groups.get("releaselevel", "")],
    groups.get("serial", ""),
)
