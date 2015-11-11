"""This file defines diff_metadata, patch_metadata, used by diff_notebooks."""

__all__ = ["diff_metadata", "patch_metadata"]

from .diff_dicts import diff_nested_dicts, patch_nested_dicts

def diff_metadata(mda, mdb):
    """Produce a diff for arbitrary notebook metadata. Compatible with patch_metadata"""
    # FIXME: This doesn't handle lists inside dict well. Replace this with some generic dict diff/patch library?
    return diff_nested_dicts(mda, mdb)

def patch_metadata(md, diff):
    """Patch notebook metadata md with diff produced by diff_metadata."""
    # FIXME: This doesn't handle lists inside dict well. Replace this with some generic dict diff/patch library?
    return patch_nested_dicts(md, diff)
