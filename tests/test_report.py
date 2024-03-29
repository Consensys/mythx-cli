import json

from click.testing import CliRunner
from mythx_models.response import AnalysisInputResponse, DetectedIssuesResponse

from mythx_cli.cli import cli

from .common import get_test_case, mock_context

INPUT_RESPONSE: AnalysisInputResponse = get_test_case(
    "testdata/analysis-input-response.json", AnalysisInputResponse
)
ISSUES_RESPONSE: DetectedIssuesResponse = get_test_case(
    "testdata/detected-issues-response.json", DetectedIssuesResponse
)
ISSUES_SIMPLE = get_test_case("testdata/detected-issues-simple.txt", raw=True)
ISSUES_TABLE = get_test_case("testdata/detected-issues-table.txt", raw=True)


def test_report_tabular():
    runner = CliRunner()
    with mock_context():
        result = runner.invoke(
            cli, ["analysis", "report", "ab9092f7-54d0-480f-9b63-1bb1508280e2"]
        )

        assert result.output == ISSUES_TABLE
        assert result.exit_code == 0


def test_report_tabular_blacklist():
    runner = CliRunner()
    with mock_context():
        result = runner.invoke(
            cli,
            [
                "analysis",
                "report",
                "--swc-blacklist",
                "SWC-110",
                "ab9092f7-54d0-480f-9b63-1bb1508280e2",
            ],
        )

        assert "Assert Violation" not in result.output
        assert (
            "/home/spoons/diligence/mythx-qa/land/contracts/estate/EstateStorage.sol"
            not in result.output
        )
        assert result.exit_code == 0


def test_report_tabular_whitelist():
    runner = CliRunner()
    with mock_context():
        result = runner.invoke(
            cli,
            [
                "analysis",
                "report",
                "--swc-whitelist",
                "SWC-110",
                "ab9092f7-54d0-480f-9b63-1bb1508280e2",
            ],
        )

        assert "Assert Violation" in result.output
        assert (
            "/home/spoons/diligence/mythx-qa/land/contracts/estate/EstateStorage.sol"
            in result.output
        )
        assert result.exit_code == 0


def test_report_tabular_filter():
    runner = CliRunner()
    with mock_context():
        result = runner.invoke(
            cli,
            [
                "analysis",
                "report",
                "--min-severity",
                "high",
                "ab9092f7-54d0-480f-9b63-1bb1508280e2",
            ],
        )

        assert "Assert Violation" not in result.output
        assert (
            "/home/spoons/diligence/mythx-qa/land/contracts/estate/EstateStorage.sol"
            not in result.output
        )
        assert result.exit_code == 0


def test_report_json():
    runner = CliRunner()
    with mock_context():
        result = runner.invoke(
            cli,
            [
                "--format",
                "json",
                "analysis",
                "report",
                "ab9092f7-54d0-480f-9b63-1bb1508280e2",
            ],
        )

        assert (
            json.loads(result.output)[0]["issue_reports"]
            == json.loads(ISSUES_RESPONSE.json())["issue_reports"]
        )
        assert result.exit_code == 0


def test_report_json_blacklist():
    runner = CliRunner()
    with mock_context():
        result = runner.invoke(
            cli,
            [
                "--format",
                "json",
                "analysis",
                "report",
                "--swc-blacklist",
                "SWC-110",
                "ab9092f7-54d0-480f-9b63-1bb1508280e2",
            ],
        )

        reports = json.loads(result.output)[0]["issue_reports"]
        for report in reports:
            for issue in report["issues"]:
                assert issue["swc_id"] != "SWC-110"

        assert result.exit_code == 0


def test_report_json_whitelist():
    runner = CliRunner()
    with mock_context():
        result = runner.invoke(
            cli,
            [
                "--format",
                "json",
                "analysis",
                "report",
                "--swc-whitelist",
                "SWC-110",
                "ab9092f7-54d0-480f-9b63-1bb1508280e2",
            ],
        )

        reports = json.loads(result.output)[0]["issue_reports"]
        for report in reports:
            for issue in report["issues"]:
                assert issue["swc_id"] == "SWC-110"

        assert result.exit_code == 0


def test_report_json_filter():
    runner = CliRunner()
    with mock_context():
        result = runner.invoke(
            cli,
            [
                "--debug",
                "--format",
                "json",
                "analysis",
                "report",
                "--min-severity",
                "high",
                "ab9092f7-54d0-480f-9b63-1bb1508280e2",
            ],
        )

        reports = json.loads(result.output)[0]["issue_reports"]
        for report in reports:
            for issue in report["issues"]:
                assert issue["swc_id"] != "SWC-110"

        assert result.exit_code == 0


def test_report_json_pretty():
    runner = CliRunner()
    with mock_context():
        result = runner.invoke(
            cli,
            [
                "--format",
                "json-pretty",
                "analysis",
                "report",
                "ab9092f7-54d0-480f-9b63-1bb1508280e2",
            ],
        )

        assert (
            json.loads(result.output)[0]["issue_reports"]
            == json.loads(ISSUES_RESPONSE.json())["issue_reports"]
        )
        assert result.exit_code == 0


def test_report_json_pretty_blacklist():
    runner = CliRunner()
    with mock_context():
        result = runner.invoke(
            cli,
            [
                "--format",
                "json-pretty",
                "analysis",
                "report",
                "--swc-blacklist",
                "SWC-110",
                "ab9092f7-54d0-480f-9b63-1bb1508280e2",
            ],
        )

        reports = json.loads(result.output)[0]["issue_reports"]
        for report in reports:
            for issue in report["issues"]:
                assert issue["swc_id"] != "SWC-110"

        assert result.exit_code == 0


def test_report_json_pretty_whitelist():
    runner = CliRunner()
    with mock_context():
        result = runner.invoke(
            cli,
            [
                "--format",
                "json-pretty",
                "analysis",
                "report",
                "--swc-whitelist",
                "SWC-110",
                "ab9092f7-54d0-480f-9b63-1bb1508280e2",
            ],
        )

        reports = json.loads(result.output)[0]["issue_reports"]
        for report in reports:
            for issue in report["issues"]:
                print(issue)
                assert issue["swc_id"] == "SWC-110"

        assert result.exit_code == 0


def test_report_json_pretty_filter():
    runner = CliRunner()
    with mock_context():
        result = runner.invoke(
            cli,
            [
                "--format",
                "json-pretty",
                "analysis",
                "report",
                "--min-severity",
                "high",
                "ab9092f7-54d0-480f-9b63-1bb1508280e2",
            ],
        )

        reports = json.loads(result.output)[0]["issue_reports"]
        for report in reports:
            for issue in report["issues"]:
                assert issue["swc_id"] != "SWC-110"

        assert result.exit_code == 0


def test_report_simple():
    runner = CliRunner()
    with mock_context():
        result = runner.invoke(
            cli,
            [
                "--format",
                "simple",
                "analysis",
                "report",
                "ab9092f7-54d0-480f-9b63-1bb1508280e2",
            ],
        )

        assert result.output == ISSUES_SIMPLE
        assert result.exit_code == 0


def test_report_simple_blacklist():
    runner = CliRunner()
    with mock_context():
        result = runner.invoke(
            cli,
            [
                "--format",
                "simple",
                "analysis",
                "report",
                "--swc-blacklist",
                "SWC-110",
                "ab9092f7-54d0-480f-9b63-1bb1508280e2",
            ],
        )

        assert "Assert Violation" not in result.output
        assert result.exit_code == 0


def test_report_simple_whitelist():
    runner = CliRunner()
    with mock_context():
        result = runner.invoke(
            cli,
            [
                "--format",
                "simple",
                "analysis",
                "report",
                "--swc-whitelist",
                "SWC-110",
                "ab9092f7-54d0-480f-9b63-1bb1508280e2",
            ],
        )
        assert "Assert Violation" in result.output
        assert result.exit_code == 0


def test_report_simple_filter():
    runner = CliRunner()
    with mock_context():
        result = runner.invoke(
            cli,
            [
                "--format",
                "simple",
                "analysis",
                "report",
                "--min-severity",
                "high",
                "ab9092f7-54d0-480f-9b63-1bb1508280e2",
            ],
        )

        assert "SWC-110" not in result.output
        assert result.exit_code == 0
