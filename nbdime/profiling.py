
"""Tools for profiling diff/merge performance.

Sometimes diffing times can become unacceptably long.
Then the tools in this module can help you profile and figure out
where the time is spent. For a more rigorous profiling, consider using
cPython, but for initial considerations these should be helpful.

Typical profiling usage:
Add some statements like
from nbdime.profiling import timer
with timer.time('Key to identify this segment'):
    <code to time>

Then, launch `python -m nbdime.profiling notebookA.ipynb notebookB.ipynb`.

Example case:
Output diffing is slow. By cPython/timer, the time spent has been narrowed
to comparison of MIME types (`_compare_mimedata()`). To figure out which
MIME type is taking all the time, the following is added to that function:

    with timer.time(mimetype):
        <existing function body>

The output becomes:

    Key           Calls          Time
    ----------  -------  ------------
    text/html         6  74.9686
    text/plain       12   0.000500202
    image/png         5   0

From this we can see that the HTML comparison is really blowing up!
Further inspection reveals that there are two html outputs in each
notebook that contain an embedded base64 image. These caused the text
diff to blow up.

"""

import time
import contextlib
from tabulate import tabulate
from functools import wraps


def _sort_time(value):
    time = value[1]['time']
    return -time


class TimePaths(object):
    def __init__(self, verbose=False, enabled=True):
        self.verbose = verbose
        self.map = {}
        self.enabled = enabled

    @contextlib.contextmanager
    def time(self, key):
        if not self.enabled:
            yield
            return
        start = time.time()
        yield
        end = time.time()
        secs = end - start
        if key in self.map:
            self.map[key]['time'] += secs
            self.map[key]['calls'] += 1
        else:
            self.map[key] = dict(time=secs, calls=1)

    def profile(self, key=None):
        def decorator(function):
            nonlocal key
            if key is None:
                key = function.__name__ or 'unknown'
            @wraps(function)
            def inner(*args, **kwargs):
                with self.time(key):
                    return function(*args, **kwargs)
            return inner
        return decorator

    @contextlib.contextmanager
    def enable(self):
        old = self.enabled
        self.enabled = True
        yield
        self.enabled = old

    @contextlib.contextmanager
    def disable(self):
        old = self.enabled
        self.enabled = False
        yield
        self.enabled = old

    def __str__(self):
        # First, sort by path
        items = sorted(self.map.items(), key=_sort_time)
        lines = []
        for key, data in items:
            time = data['time']
            calls = data['calls']
            lines.append((key, calls, time, time / calls))
        return tabulate(lines, headers=['Key', 'Calls', 'Time', 'Time/Call'])


timer = TimePaths(enabled=False)


def profile_diff_paths(args=None):
    import nbdime.nbdiffapp
    import nbdime.profiling
    try:
        with nbdime.profiling.timer.enable():
            nbdime.nbdiffapp.main(args)
    finally:
        data = str(nbdime.profiling.timer)
        print(data)


if __name__ == "__main__":
    profile_diff_paths()
