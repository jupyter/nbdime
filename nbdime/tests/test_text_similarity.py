# coding: utf-8

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

import pytest

from nbdime.diffing.generic import (
    compare_strings_approximate,
)

def test_similarity_threshold_is_configurable():
    base = (
        "lorem ipsum dolor sit amet consectetur adipiscing elit "
        "sed do eiusmod tempor incididunt ut labore et dolore magna aliqua."
    )
    noisy = (
        "lorem ipsum dolor sit amet consectetur adipiscing elit "
        "A LONG INSERTED SEGMENT WITH MANY EXTRA WORDS TO REDUCE SIMILARITY "
        "sed do eiusmod tempor incididunt ut labore et dolore magna aliqua."
    )
    assert not compare_strings_approximate(base, noisy, threshold=0.85)

    assert compare_strings_approximate(base, noisy, threshold=0.6)


def test_configurable_similarity_thresholds_with_long_texts():
    base = (
        "lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod tempor "
        "incididunt ut labore et dolore magna aliqua."
    )
    noisy = (
        "lorem ipsum dolor sit amet consectetur adipiscing elit "
        "A LONG INSERTED SEGMENT WITH MANY EXTRA WORDS TO REDUCE SIMILARITY "
        "sed do eiusmod tempor incididunt ut labore et dolore magna aliqua."
    )
    assert not compare_strings_approximate(base, noisy, threshold=0.85)

    assert compare_strings_approximate(base, noisy, threshold=0.6)


def test_requires_contiguous_overlap():
    # Scattered single-character matches with no 5-character overlap should not qualify as similar.
    scattered_left = (
        "alpha bravo charlie delta echo foxtrot golf hotel india juliet kilo lima mike november oscar"
    )
    scattered_right = (
        "alp_ha-bra_vo-char_lie-del_ta-ech_o-fox_tro_t-gol_f-hot_el-ind_ia-jul_iet-"
        "kil_o-lim_a-mik_e-nov_em-ber_osc_ar"
    )
    assert not compare_strings_approximate(scattered_left, scattered_right, threshold=0.3, min_match_length_to_be_similar=5)

    # Genuine overlap of multiple characters still counts as similar.
    left = "value=3.14159\nnote about measuring pi\n"
    right = "value=3.14159\nnote about measuring pi!\n"
    assert compare_strings_approximate(left, right, threshold=0.3, min_match_length_to_be_similar=5)


def test_multiline_short_text_requires_real_similarity():

    local = "local community science projects gather data daily across regions"
    remote = "remote venture capital funds acquire startup assets globally"
    assert not compare_strings_approximate(local, remote, threshold=0.3)


def test_short_strings_with_overlap_and_small_diff_are_similar():
    left = "short-text-123"
    right = "short-text-XYZ"
    assert compare_strings_approximate(left, right, threshold=0.5)


def test_short_strings_without_overlap_are_different_even_if_small_diff():
    left = "abcde12345"
    right = "vwxyz67890"
    assert not compare_strings_approximate(left, right, threshold=0.5)


def test_short_strings_with_overlap_but_large_diff_are_different():
    left = "hello-world"
    right = "hello-everyone-this-is-longer"
    assert not compare_strings_approximate(left, right, threshold=0.5)
