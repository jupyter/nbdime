
import copy

from .validation import error_invalid_diff_entry, is_valid_diff

__all__ = ["diff"]


def diff(a, b):
    d = []

    assert is_valid_diff(d)
    return d
