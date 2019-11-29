import json
from unittest.mock import patch

from click.testing import CliRunner

from mythx_cli.cli import cli
from mythx_models.response import AnalysisInputResponse, DetectedIssuesResponse
from .common import get_test_case

INPUT_RESPONSE = get_test_case("testdata/analysis-input-response.json", AnalysisInputResponse)
ISSUES_RESPONSE = get_test_case("testdata/detected-issues-response.json", DetectedIssuesResponse)
ISSUES_SIMPLE = get_test_case("testdata/detected-issues-simple.txt", raw=True)
ISSUES_TABLE = get_test_case("testdata/detected-issues-table.txt", raw=True)


def test_report_tabular():
    runner = CliRunner()
    with patch("pythx.Client.report") as report_patch, patch(
        "pythx.Client.request_by_uuid"
    ) as input_patch:
        report_patch.return_value = ISSUES_RESPONSE
        input_patch.return_value = INPUT_RESPONSE
        result = runner.invoke(cli, ["report", "ab9092f7-54d0-480f-9b63-1bb1508280e2"])
        assert result.exit_code == 0
        assert result.output == ISSUES_TABLE


def test_report_json():
    runner = CliRunner()
    with patch("pythx.Client.report") as report_patch, patch(
        "pythx.Client.request_by_uuid"
    ) as input_patch:
        report_patch.return_value = ISSUES_RESPONSE
        input_patch.return_value = INPUT_RESPONSE
        result = runner.invoke(
            cli, ["--format", "json", "report", "ab9092f7-54d0-480f-9b63-1bb1508280e2"]
        )
        assert result.exit_code == 0
        assert json.loads(result.output) == json.loads(ISSUES_RESPONSE.to_json())


def test_report_json_pretty():
    runner = CliRunner()
    with patch("pythx.Client.report") as report_patch, patch(
        "pythx.Client.request_by_uuid"
    ) as input_patch:
        report_patch.return_value = ISSUES_RESPONSE
        input_patch.return_value = INPUT_RESPONSE
        result = runner.invoke(
            cli,
            [
                "--format",
                "json-pretty",
                "report",
                "ab9092f7-54d0-480f-9b63-1bb1508280e2",
            ],
        )
        assert result.exit_code == 0
        assert json.loads(result.output) == json.loads(ISSUES_RESPONSE.to_json())


def test_report_simple():
    runner = CliRunner()
    with patch("pythx.Client.report") as report_patch, patch(
        "pythx.Client.request_by_uuid"
    ) as input_patch:
        report_patch.return_value = ISSUES_RESPONSE
        input_patch.return_value = INPUT_RESPONSE
        result = runner.invoke(
            cli,
            ["--format", "simple", "report", "ab9092f7-54d0-480f-9b63-1bb1508280e2"],
        )
        assert result.exit_code == 0
        assert result.output == ISSUES_SIMPLE
