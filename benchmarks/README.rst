Notebook diff benchmarks
========================

These optional Airspeed Velocity (ASV) benchmarks measure ``diff_notebooks``
on deterministic synthetic inputs. They provide reproducible workloads for
`issue #826 <https://github.com/jupyter/nbdime/issues/826>`_; they do not claim
to reproduce the unavailable notebooks from earlier performance reports.

Workloads
---------

* ``Cells``: 100, 500 and 1000 cells, with a middle-cell edit or reversed order,
  both with modern cell IDs and without IDs (notebook format 4.4).
* ``StreamOutput``: 1000, 10000 and 50000 output lines, with a change every
  hundred lines. Unique and repeated lines exercise different text matching
  behavior.
* ``ImageOutput``: 15 cells and roughly 1, 4 or 13 MiB of base64 PNG data.
  Compare a source-only edit with an entirely changed image. The PNG is valid
  and generated with the standard library; no kernel execution or downloads
  are required.

Setup generates and validates the inputs, then checks that applying the diff
reconstructs the target notebook. Setup is excluded from timing. Unchanged
strings have separate identities in the two inputs, as they would when read
from separate files. The setup check warms the inputs before measurement.
These measure steady-state diff computation, not notebook loading, patch
application or browser rendering.

Running
-------

From an environment with a development installation of nbdime::

    python -m pip install asv
    asv machine --yes
    asv check --python=same
    asv run --python=same --quick --show-stderr --dry-run

``asv machine --yes`` records the current machine with detected defaults;
run it once per machine, including a fresh non-interactive CI runner.

The quick run is a smoke check, not a performance measurement. For timings in
the current environment, omit ``--quick``. Use ``--bench StreamOutput`` (or
another benchmark name) to narrow the workload. ASV uses a 120-second process
timeout for ``Cells`` and 30 seconds for the other workloads. These limits
include setup, warmup and repeated samples, not just a single diff.

To compare committed versions, ASV can build its own Python environments::

    asv continuous BASE_COMMIT HEAD_COMMIT

This uses the project's normal build process, including its Node.js/frontend
build requirements. The default configuration uses Python 3.12; override the
environment when comparing revisions with different Python requirements.

Keep comparisons on the same machine and dependency versions, without other
CPU-intensive work. Report the commits, Python/dependency versions and ASV
parameters with results. No timing threshold is imposed on the normal test
suite. ASV's environments, measurements and generated reports stay under
``.asv/`` and are not committed.
