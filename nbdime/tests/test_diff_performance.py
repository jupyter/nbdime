
import pytest

import random
import string

from .utils import outputs_to_notebook

from nbdime.diffing import diff_notebooks


def random_string(N):
    return ''.join(random.choice(
        string.ascii_uppercase + string.digits) for _ in range(N))


@pytest.mark.timeout(timeout=20)
def test_text_mimedata_performance():
    # Create some random text (seeded) for a few
    # outputs on each side
    random.seed(0)
    base = outputs_to_notebook([
        [random_string(50000)],
        [random_string(80000)],
        [random_string(30000)],
    ])
    remote = outputs_to_notebook([
        [random_string(50000)],
        [random_string(30000)],
        [random_string(30000)],
        [random_string(80000)],
    ])

    # Since the contents is random, ignore the actual diff
    # Only interested in performance not blowing up
    diff_notebooks(base, remote)

