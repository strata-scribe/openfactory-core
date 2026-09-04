import os
import ast
import tempfile
from pathlib import Path
from unittest import mock
import pytest

from openfactory import environ

def test_env_name_shape_valid():
    assert environ.ENV_NAME_SHAPE.match("OPENFACTORY_HOME")
    assert environ.ENV_NAME_SHAPE.match("AWS_REGION")
    assert environ.ENV_NAME_SHAPE.match("A_B")
    assert environ.ENV_NAME_SHAPE.match("MY_VAR_123")

def test_env_name_shape_invalid():
    assert not environ.ENV_NAME_SHAPE.match("HOME")  # no underscore
    assert not environ.ENV_NAME_SHAPE.match("OPENFACTORY") # no underscore
    assert not environ.ENV_NAME_SHAPE.match("OPENFACTORY_") # trailing underscore
    assert not environ.ENV_NAME_SHAPE.match("_OPENFACTORY") # leading underscore
    assert not environ.ENV_NAME_SHAPE.match("OpenFactory_Home") # mixed case
    assert not environ.ENV_NAME_SHAPE.match("openfactory_home") # lower case
    assert not environ.ENV_NAME_SHAPE.match("1_VAR") # starts with number

def test_not_declared_exception():
    exc = environ.NotDeclared("missing region")
    assert isinstance(exc, RuntimeError)
    assert str(exc) == "missing region"

@mock.patch.dict(os.environ, {"AWS_DEFAULT_REGION": "us-east-1", "AWS_REGION": "us-west-2"})
def test_cloud_region_prioritizes_default_region():
    assert environ.cloud_region() == "us-east-1"

@mock.patch.dict(os.environ, {"AWS_REGION": "us-west-2"})
def test_cloud_region_reads_region():
    assert environ.cloud_region() == "us-west-2"

@mock.patch.dict(os.environ, {"AWS_REGION": "  us-west-2  "})
def test_cloud_region_strips_whitespace():
    assert environ.cloud_region() == "us-west-2"

@mock.patch.dict(os.environ, clear=True)
def test_cloud_region_empty_not_required():
    assert environ.cloud_region() == ""

@mock.patch.dict(os.environ, clear=True)
def test_cloud_region_empty_required():
    with pytest.raises(environ.NotDeclared, match="this deployment does not say which cloud region"):
        environ.cloud_region(required=True)

@mock.patch.dict(os.environ, {"OPENFACTORY_SSM_PREFIX": "/my/prefix/"})
def test_ssm_prefix_strips_trailing_slash():
    assert environ.ssm_prefix() == "/my/prefix"

@mock.patch.dict(os.environ, {"OPENFACTORY_SSM_PREFIX": "  /my/prefix  "})
def test_ssm_prefix_strips_whitespace():
    assert environ.ssm_prefix() == "/my/prefix"

@mock.patch.dict(os.environ, clear=True)
def test_ssm_prefix_empty():
    assert environ.ssm_prefix() == ""

def test_names_read_shapes(tmp_path):
    environ.names_read.cache_clear()

    # Create some dummy python files with different shapes of env var reads
    file1 = tmp_path / "file1.py"
    file1.write_text("""
import os

# Shape 1: Literal keys
os.environ.get("OPENFACTORY_LITERAL_GET")
os.environ["OPENFACTORY_LITERAL_SUB"]
os.getenv("OPENFACTORY_LITERAL_GETENV")

# Shape 2: Collections of env-shaped strings (names table)
REQUIRED = ("OPENFACTORY_REQ_1", "OPENFACTORY_REQ_2")
DICT_TABLE = {"a": "OPENFACTORY_DICT_1", "b": "OPENFACTORY_DICT_2"}
SET_TABLE = {"OPENFACTORY_SET_1"}
LIST_TABLE = ["OPENFACTORY_LIST_1"]

# Shape 4: Module-level bound variables
MY_VAR = "OPENFACTORY_BOUND_VAR"
os.environ.get(MY_VAR)
""")

    file2 = tmp_path / "file2.py"
    file2.write_text("""
import os

# Shape 3: Functions that read their parameter from the environment
def read_param(key_name):
    return os.environ.get(key_name)

read_param("OPENFACTORY_PARAM_1")
read_param("OPENFACTORY_PARAM_2")
""")

    read_vars = environ.names_read(tmp_path)

    expected_vars = {
        "OPENFACTORY_LITERAL_GET",
        "OPENFACTORY_LITERAL_SUB",
        "OPENFACTORY_LITERAL_GETENV",
        "OPENFACTORY_REQ_1",
        "OPENFACTORY_REQ_2",
        "OPENFACTORY_DICT_1",
        "OPENFACTORY_DICT_2",
        "OPENFACTORY_SET_1",
        "OPENFACTORY_LIST_1",
        "OPENFACTORY_BOUND_VAR",
        "OPENFACTORY_PARAM_1",
        "OPENFACTORY_PARAM_2"
    }

    assert read_vars == expected_vars

def test_reserved_logic(tmp_path):
    environ.names_read.cache_clear()

    # Create a dummy file that reads some variables
    f = tmp_path / "dummy.py"
    f.write_text("""
import os
os.environ.get("SOME_FOREIGN_VAR")
""")

    # Reserved because it's under our prefix
    reason = environ.reserved("OPENFACTORY_NEW_VAR", root=tmp_path)
    assert reason and "under OPENFACTORY_*" in reason

    # Reserved because it's under the retired prefix
    reason = environ.reserved(environ.RETIRED_ENV_PREFIX + "OLD_VAR", root=tmp_path)
    assert reason and f"under {environ.RETIRED_ENV_PREFIX}*" in reason

    # Reserved because it's in the names_read (foreign tool variable)
    reason = environ.reserved("SOME_FOREIGN_VAR", root=tmp_path)
    assert reason and "read with the meaning that tool gives it" in reason

    # Not reserved
    assert environ.reserved("SOME_OTHER_VAR", root=tmp_path) is None

def test_reserved_no_sources(tmp_path):
    environ.names_read.cache_clear()

    # Empty directory, no sources
    reason = environ.reserved("SOME_VAR", root=tmp_path)
    assert reason and "unverifiable: this installation ships no readable sources" in reason
