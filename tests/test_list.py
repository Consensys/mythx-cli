import json
from unittest.mock import patch

from click.testing import CliRunner

from mythx_cli.cli import cli
from mythx_models.response import AnalysisListResponse, GroupListResponse

from .common import get_test_case

GROUP_LIST = get_test_case("testdata/group-list-response.json", GroupListResponse)
GROUP_LIST_SIMPLE = get_test_case("testdata/group-list-simple.txt", raw=True)
GROUP_LIST_TABLE = get_test_case("testdata/group-list-table.txt", raw=True)
ANALYSIS_LIST = get_test_case(
    "testdata/analysis-list-response.json", AnalysisListResponse
)
ANALYSIS_LIST_SIMPLE = get_test_case("testdata/analysis-list-simple.txt", raw=True)
ANALYSIS_LIST_TABLE = get_test_case("testdata/analysis-list-table.txt", raw=True)


def test_list_tabular():
    runner = CliRunner()
    with patch("pythx.Client.analysis_list") as list_patch:
        list_patch.return_value = ANALYSIS_LIST
        result = runner.invoke(cli, ["list"])
        assert result.exit_code == 0
        assert result.output == ANALYSIS_LIST_TABLE


def test_group_list_tabular():
    runner = CliRunner()
    with patch("pythx.Client.group_list") as list_patch:
        list_patch.return_value = GROUP_LIST
        result = runner.invoke(cli, ["group", "list"])
        assert result.exit_code == 0
        assert result.output == GROUP_LIST_TABLE


def test_list_json():
    runner = CliRunner()
    with patch("pythx.Client.analysis_list") as list_patch:
        list_patch.return_value = ANALYSIS_LIST
        result = runner.invoke(cli, ["--format", "json", "list"])
        assert result.exit_code == 0
        assert json.loads(result.output) == ANALYSIS_LIST.to_dict()


def test_group_list_json():
    runner = CliRunner()
    with patch("pythx.Client.group_list") as list_patch:
        list_patch.return_value = GROUP_LIST
        result = runner.invoke(cli, ["--format", "json", "group", "list"])
        assert result.exit_code == 0
        assert json.loads(result.output) == GROUP_LIST.to_dict()


def test_list_json_pretty():
    runner = CliRunner()
    with patch("pythx.Client.analysis_list") as list_patch:
        list_patch.return_value = ANALYSIS_LIST
        result = runner.invoke(cli, ["--format", "json-pretty", "list"])
        assert result.exit_code == 0
        assert json.loads(result.output) == ANALYSIS_LIST.to_dict()


def test_group_list_json_pretty():
    runner = CliRunner()
    with patch("pythx.Client.group_list") as list_patch:
        list_patch.return_value = GROUP_LIST
        result = runner.invoke(cli, ["--format", "json-pretty", "group", "list"])
        assert result.exit_code == 0
        assert json.loads(result.output) == GROUP_LIST.to_dict()


def test_list_simple():
    runner = CliRunner()
    with patch("pythx.Client.analysis_list") as list_patch:
        list_patch.return_value = ANALYSIS_LIST
        result = runner.invoke(cli, ["--format", "simple", "list"])
        assert result.exit_code == 0
        assert result.output == ANALYSIS_LIST_SIMPLE


def test_group_list_simple():
    runner = CliRunner()
    with patch("pythx.Client.group_list") as list_patch:
        list_patch.return_value = GROUP_LIST
        result = runner.invoke(cli, ["--format", "simple", "group", "list"])
        assert result.exit_code == 0
        assert result.output == GROUP_LIST_SIMPLE
