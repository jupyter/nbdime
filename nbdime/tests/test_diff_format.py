from jsonschema import Draft4Validator as Validator
from nbdime import diff, diff_notebooks


def test_check_schema(json_schema_diff):
    Validator.check_schema(json_schema_diff)


def test_validate_obj_diff(diff_validator):
    a = {"foo": [1, 2, 3], "bar": {"ting": 7, "tang": 123}}
    b = {"foo": [1, 3, 4], "bar": {"tang": 126, "hello": "world"}}
    d = diff(a, b)

    diff_validator.validate(d)


def test_validate_array_diff(diff_validator):
    a = [2, 3, 4]
    b = [1, 2, 4, 6]
    d = diff(a, b)

    diff_validator.validate(d)


def test_validate_matching_notebook_diff(matching_nb_pairs, diff_validator):
    a, b = matching_nb_pairs
    d = diff_notebooks(a, b)

    diff_validator.validate(d)
