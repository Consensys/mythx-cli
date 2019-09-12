import json
from unittest.mock import patch

from click.testing import CliRunner
from mythx_models.response import AnalysisListResponse

from mythx_cli.cli import cli

from .testdata import LIST_RESPONSE_OBJ, LIST_RESPONSE_SIMPLE


def test_list_simple():
    runner = CliRunner()
    with patch("pythx.Client.analysis_list") as list_patch:
        list_patch.return_value = LIST_RESPONSE_OBJ
        result = runner.invoke(cli, ["list"])
        assert result.exit_code == 0
        assert result.output == LIST_RESPONSE_SIMPLE


def test_list_json():
    runner = CliRunner()
    with patch("pythx.Client.analysis_list") as list_patch:
        list_patch.return_value = LIST_RESPONSE_OBJ
        result = runner.invoke(cli, ["--format", "json", "list"])
        assert result.exit_code == 0
        assert json.loads(result.output) == LIST_RESPONSE_OBJ.to_dict()


def test_list_json_pretty():
    runner = CliRunner()
    with patch("pythx.Client.analysis_list") as list_patch:
        list_patch.return_value = LIST_RESPONSE_OBJ
        result = runner.invoke(cli, ["--format", "json-pretty", "list"])
        assert result.exit_code == 0
        assert json.loads(result.output) == LIST_RESPONSE_OBJ.to_dict()
