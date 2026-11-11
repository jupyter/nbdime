"""Deterministic notebook diff workloads, motivated by issue #826."""

import base64
import json
import random
import struct
import zlib

import nbformat
from nbformat.v4 import new_code_cell, new_notebook, new_output

from nbdime.diffing import diff_notebooks
from nbdime.patching import patch_notebook


def copy_notebook(notebook):
    # Unlike deepcopy, a JSON round trip gives unchanged strings separate
    # identities, as when reading the two notebooks from different files.
    return nbformat.from_dict(json.loads(json.dumps(notebook)))


def check_diff(base, remote):
    nbformat.validate(base)
    nbformat.validate(remote)
    assert patch_notebook(base, diff_notebooks(base, remote)) == remote


class Cells:
    params = [[100, 500, 1000], ['edit', 'reverse'], [True, False]]
    param_names = ['cell_count', 'change', 'cell_ids']
    # The limit covers setup, warmup and all timing samples together.
    timeout = 120

    def setup(self, cell_count, change, cell_ids):
        self.base = new_notebook(cells=[
            new_code_cell(f'value = {i}\nprint(value)\n', id=f'cell-{i}')
            for i in range(cell_count)
        ])
        if not cell_ids:
            self.base.nbformat_minor = 4
            for cell in self.base.cells:
                del cell['id']
        self.remote = copy_notebook(self.base)
        if change == 'edit':
            self.remote.cells[cell_count // 2].source += 'print(value + 1)\n'
        else:
            self.remote.cells.reverse()
        check_diff(self.base, self.remote)

    def time_diff(self, cell_count, change, cell_ids):
        diff_notebooks(self.base, self.remote)


class StreamOutput:
    params = [[1000, 10000, 50000], ['unique', 'repeated']]
    param_names = ['line_count', 'lines']
    timeout = 30

    def setup(self, line_count, lines):
        if lines == 'unique':
            text = ''.join(f'iteration {i:06d}: value = {i % 97}\n'
                           for i in range(line_count))
        else:
            text = 'iteration complete\n' * line_count
        self.base = new_notebook(cells=[new_code_cell(
            'run_experiment()\n', id='stream', outputs=[
                new_output('stream', name='stdout', text=text),
            ],
        )])
        self.remote = copy_notebook(self.base)
        changed = self.remote.cells[0].outputs[0].text.splitlines(keepends=True)
        for index in range(0, line_count, 100):
            changed[index] = 'iteration changed\n'
        self.remote.cells[0].outputs[0].text = ''.join(changed)
        check_diff(self.base, self.remote)

    def time_diff(self, line_count, lines):
        diff_notebooks(self.base, self.remote)


def png_data(height, seed):
    """Generate a valid RGB PNG without requiring plotting/image packages."""
    width = 1024
    rng = random.Random(seed)
    pixels = b''.join(b'\0' + rng.randbytes(width * 3) for _ in range(height))

    def chunk(kind, data):
        return (struct.pack('!I', len(data)) + kind + data
                + struct.pack('!I', zlib.crc32(kind + data)))

    image = (b'\x89PNG\r\n\x1a\n'
             + chunk(b'IHDR', struct.pack('!2I5B', width, height, 8, 2, 0, 0, 0))
             + chunk(b'IDAT', zlib.compress(pixels, level=0))
             + chunk(b'IEND', b''))
    return base64.b64encode(image).decode('ascii')


class ImageOutput:
    params = [[1, 4, 13], ['source', 'image']]
    param_names = ['image_mib', 'change']
    timeout = 30

    def setup(self, image_mib, change):
        self.base = new_notebook(cells=[
            new_code_cell(f'value = {i}\n', id=f'image-cell-{i}')
            for i in range(15)
        ])
        self.base.cells[7].outputs = [new_output(
            'display_data', data={'image/png': png_data(256 * image_mib, 0)},
        )]
        self.remote = copy_notebook(self.base)
        if change == 'source':
            self.remote.cells[7].source += '# updated caption\n'
        else:
            self.remote.cells[7].outputs[0].data['image/png'] = png_data(
                256 * image_mib, 1)
        check_diff(self.base, self.remote)

    def time_diff(self, image_mib, change):
        diff_notebooks(self.base, self.remote)
