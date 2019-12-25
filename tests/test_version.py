import json
from unittest.mock import patch

from click.testing import CliRunner

from mythx_cli.cli import cli
from mythx_models.response import VersionResponse

from .common import get_test_case, mock_context

VERSION_RESPONSE = get_test_case("testdata/version-response.json", VersionResponse)
VERSION_SIMPLE = get_test_case("testdata/version-simple.txt", raw=True)
VERSION_TABLE = get_test_case("testdata/version-table.txt", raw=True)


def test_version_tabular():
    runner = CliRunner()
    with mock_context():
        result = runner.invoke(cli, ["version"])
        assert result.exit_code == 0
        assert result.output == VERSION_TABLE


def test_version_json():
    runner = CliRunner()
    with mock_context():
        result = runner.invoke(cli, ["--format", "json", "version"])
        assert result.exit_code == 0
        assert json.loads(result.output) == VERSION_RESPONSE.to_dict()


def test_version_json_pretty():
    runner = CliRunner()
    with mock_context():
        result = runner.invoke(cli, ["--format", "json-pretty", "version"])
        assert result.exit_code == 0
        assert json.loads(result.output) == VERSION_RESPONSE.to_dict()


def test_version_simple():
    runner = CliRunner()
    with mock_context():
        result = runner.invoke(cli, ["--format", "simple", "version"])
        assert result.exit_code == 0
        print(result.output)
        assert result.output == VERSION_SIMPLE
