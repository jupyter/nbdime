from __future__ import unicode_literals
from __future__ import print_function

try:
    from base64 import encodebytes
except ImportError:
    from base64 import encodestring as encodebytes
import os
from pprint import pformat
try:
    from unittest import mock
except ImportError:
    import mock

from nbformat import v4

from nbdime import prettyprint as pp
from nbdime.diffing import diff


def b64text(nbytes):
    """Return n bytes as base64-encoded text"""
    return encodebytes(os.urandom(nbytes)).decode('ascii')


def test_present_dict_no_markup():
    d = {
        'a': 5,
        'b': [1, 2, 3],
        'c': {
            'x': 'y',
        },
        'd': 10,
        'short': 'text',
        'long': 'long\ntext',
    }
    prefix = '-'
    lines = pp.present_dict_no_markup(prefix, d, exclude_keys={'d',})
    text = '\n'.join(lines)
    print(text)
    for key in d:
        if key != 'd':
            mark = '-%s:' % key
            assert mark in text
    assert "short: text" in text
    assert 'long:\n' in text
    assert 'd:' not in text

def test_present_multiline_string_b64():
    ins = b64text(1024)
    prefix = '+'
    lines = pp.present_multiline_string(prefix, ins)
    assert len(lines) == 1
    line = lines[0]
    assert line.startswith(prefix)
    assert len(line) < 100
    assert 'snip base64' in line

def test_present_multiline_string_short():
    ins = 'short string'
    prefix = '+'
    lines = pp.present_multiline_string(prefix, ins)
    assert lines == [prefix + ins]

def test_present_multiline_string_long():
    ins = '\n'.join('line %i' % i for i in range(64))
    prefix = '+'
    lines = pp.present_multiline_string(prefix, ins)
    assert len(lines) == 64
    assert (prefix + 'line 32') in lines

def test_present_value_int():
    lines = pp.present_value('+', 5)
    assert lines == ['+5']

def test_present_value_str():
    lines = pp.present_value('+', 'x')
    assert lines == ['+x']

def test_present_value_dict():
    d = {'key': 5}
    lines = pp.present_value('+', d)
    assert '\n'.join(lines) == '+' + pformat(d)

def test_present_value_list():
    lis = ['a', 'b']
    lines = pp.present_value('+', lis)
    assert '\n'.join(lines) == '+' + pformat(lis)

def test_present_stream_output():
    output = v4.new_output('stream', name='stdout', text='some\ntext')
    lines = pp.present_value('+', output, '/cells/0/outputs/3')
    assert lines == [
        '+output_type: stream',
        "+name: stdout",
        "+text:",
        "+  some",
        "+  text",
    ]

def test_present_display_data():
    output = v4.new_output('display_data', {
        'text/plain': 'text',
        'image/png': b64text(1024),
    })
    lines = pp.present_value('+', output, '/cells/0/outputs/3')
    text = '\n'.join(lines)
    assert 'output_type: display_data' in text
    assert len(text) < 500
    assert 'snip base64' in text
    assert 'image/png' in text
    assert "text/plain: text" in text
    assert all(line.startswith('+') for line in lines if line)

def test_present_markdown_cell():
    cell = v4.new_markdown_cell(source='# Heading\n\n*some markdown*')
    lines = pp.present_value('+', cell, '/cells/0')
    text = '\n'.join(lines)
    assert lines[0] == ''
    assert lines[1] == '+markdown cell:'
    assert all(line.startswith('+') for line in lines if line)
    assert 'source:' in text
    assert '# Heading' in text
    assert '' in lines
    assert '*some markdown*' in text

def test_present_code_cell():
    cell = v4.new_code_cell(source='def foo()',
        outputs=[
            v4.new_output('stream', name='stdout', text='some\ntext'),
            v4.new_output('display_data', {'text/plain': 'hello display'}),
        ]
    )
    lines = pp.present_value('+', cell, '/cells/0')
    assert lines[0] == ''
    assert lines[1] == '+code cell:'


def test_present_dict_diff(nocolor):
    a = {'a': 1}
    b = {'a': 2}
    di = diff(a, b, path='x/y')
    lines = pp.present_diff(a, di, path='x/y')
    indent = '  ' if pp.with_indent else ''
    assert lines == [ indent + line for line in [
        'replace at x/y/a:',
        '-1',
        '+2',
    ]]

def test_present_list_diff(nocolor):
    a = [1]
    b = [2]
    path = 'a/b'
    di = diff(a, b, path=path)
    lines = pp.present_diff(a, di, path=path)
    indent = '  ' if pp.with_indent else ''
    assert lines == [ indent + line for line in [
        'insert before a/b/0:',
        '+[2]',
        'delete a/b/0:',
        '-[1]',
    ]]

def test_present_string_diff():
    a = '\n'.join(['line 1', 'line 2', 'line 3', ''])
    b = '\n'.join(['line 1', 'line 3', 'line 4', ''])
    path = 'a/b'
    di = diff(a, b, path=path)
    with mock.patch('nbdime.prettyprint.which', lambda cmd: None):
        lines = pp.present_diff(a, di, path=path)
    text = '\n'.join(lines)
    assert ('< line 2' in text) or ((pp.REMOVE + 'line 2' + pp.RESET) in text)
    assert ('> line 4' in text) or ((pp.ADD + 'line 4' + pp.RESET) in text)

def test_present_string_diff_b64():
    a = b64text(1024)
    b =  b64text(800)
    path = 'a/b'
    di = diff(a, b, path=path)
    lines = pp.present_diff(a, di, path=path)
    trim_header = int(not pp.with_indent)
    indent = '  ' * pp.with_indent
    assert lines[trim_header:] == [indent + '<base64 data changed>']
