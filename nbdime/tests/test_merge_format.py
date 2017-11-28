
from jsonschema import Draft4Validator as Validator
from nbdime import decide_merge
from nbdime.merging.notebooks import decide_notebook_merge


def test_check_schema(json_schema_merge):
    Validator.check_schema(json_schema_merge)


def test_validate_obj_merge(merge_validator):
    b = {"p": {"b": 1}}
    l = {"p": {"b": 1}, "n": {"s": 7, "l": 2}}
    r = {"p": {"b": 1}, "n": {"s": 7, "r": 3}}
    decisions = decide_merge(b, l, r)

    merge_validator.validate(decisions)


def test_validate_array_merge(merge_validator):
    b = [1, 9]
    l = [1, 2, 7, 9]
    r = [1, 3, 7, 9]
    decisions = decide_merge(b, l, r)

    merge_validator.validate(decisions)


def test_validate_matching_notebook_merge(matching_nb_triplets, merge_validator, reset_log):
    base, local, remote = matching_nb_triplets
    decisions = decide_notebook_merge(base, local, remote)

    merge_validator.validate(decisions)
