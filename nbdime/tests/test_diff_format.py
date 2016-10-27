
import pytest
import json
import io
import os
from jsonschema import ValidationError
from jsonschema import Draft4Validator as Validator
from nbdime import diff, diff_notebooks
from .fixtures import matching_nb_pairs


schema_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture
def schema_json(request):
    schema_path = os.path.join(schema_dir, 'diff_format.schema.json')
    with io.open(schema_path, encoding="utf8") as f:
        schema_json = json.load(f)
    return schema_json


@pytest.fixture
def validator(request, schema_json):
    return Validator(schema_json)


def test_check_schema(schema_json):
    Validator.check_schema(schema_json)


def test_validate_obj_diff(validator):
    a = { "foo": [1,2,3], "bar": {"ting": 7, "tang": 123 } }
    b = { "foo": [1,3,4], "bar": {"tang": 126, "hello": "world" } }
    d = diff(a, b)

    validator.validate(d)


def test_validate_array_diff(validator):
    a = [2, 3, 4]
    b = [1, 2, 4, 6]
    d = diff(a, b)

    validator.validate(d)


def test_validate_matching_notebook_diff(matching_nb_pairs, validator):
    a, b = matching_nb_pairs
    d = diff_notebooks(a, b)

    validator.validate(d)
