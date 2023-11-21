# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

import re
from collections import namedtuple

VersionInfo = namedtuple("VersionInfo", ["major", "minor", "micro", "releaselevel", "serial"])

_specifier_ = {"a": "alpha", "b": "beta", "rc": "candidate", "": "final"}

__version__ = "4.0.1"

parser = re.compile(
    r"^(?P<major>\d+)\.(?P<minor>\d+)\.(?P<micro>\d+)((?P<releaselevel>[A-z]+)(?P<serial>\d+))?$"
)

parsed_version = parser.match(__version__)
groups = parsed_version.groupdict()

release_level = groups.get("releaselevel", "") or ""

version_info = VersionInfo(
    int(groups["major"]),
    int(groups["minor"]),
    int(groups["micro"]),
    # This will be whatever word is set to ensure `final`
    # is only set when releaselevel pattern is not found
    _specifier_.get(release_level, release_level),
    groups.get("serial", ""),
)
