from copy import deepcopy

from click.testing import CliRunner

from mythx_cli.cli import cli
from mythx_models.response import (
    AnalysisInputResponse,
    AnalysisSubmissionResponse,
    DetectedIssuesResponse,
    Severity,
)

from .common import get_test_case, mock_context

FORMAT_ERROR = "Could not interpret argument lolwut as bytecode or Solidity file"
SUBMISSION_RESPONSE = get_test_case(
    "testdata/analysis-submission-response.json", AnalysisSubmissionResponse
)
ISSUES_RESPONSE = get_test_case(
    "testdata/detected-issues-response.json", DetectedIssuesResponse
)
INPUT_RESPONSE = get_test_case(
    "testdata/analysis-input-response.json", AnalysisInputResponse
)


def test_bytecode_analyze():
    runner = CliRunner()
    with mock_context():
        result = runner.invoke(cli, ["analyze", "0xfe"])
        assert result.exit_code == 0
        assert INPUT_RESPONSE.source_list[0] in result.output


def test_bytecode_analyze_file_output():
    runner = CliRunner()
    with mock_context(), runner.isolated_filesystem():
        result = runner.invoke(cli, ["--output", "test.log", "analyze", "0xfe"])
        assert result.exit_code == 0
        with open("test.log") as f:
            assert INPUT_RESPONSE.source_list[0] in f.read()


def test_bytecode_analyze_ci():
    runner = CliRunner()
    with mock_context() as patches:
        # set up high-severity issue
        issues_resp = deepcopy(ISSUES_RESPONSE)
        issues_resp.issue_reports[0].issues[0].severity = Severity.HIGH
        patches[2].return_value = issues_resp

        result = runner.invoke(cli, ["--ci", "analyze", "0xfe"])
        assert result.exit_code == 1
        assert INPUT_RESPONSE.source_list[0] in result.output


def test_bytecode_analyze_blacklist():
    runner = CliRunner()
    with mock_context():
        result = runner.invoke(cli, ["analyze", "--swc-blacklist", "SWC-110", "0xfe"])
        assert result.exit_code == 0
        assert "Assert Violation" not in result.output
        assert (
            "/home/spoons/diligence/mythx-qa/land/contracts/estate/EstateStorage.sol"
            not in result.output
        )


def test_bytecode_analyze_filter():
    runner = CliRunner()
    with mock_context():
        result = runner.invoke(cli, ["analyze", "--min-severity", "high", "0xfe"])
        assert result.exit_code == 0
        assert "Assert Violation" not in result.output
        assert (
            "/home/spoons/diligence/mythx-qa/land/contracts/estate/EstateStorage.sol"
            not in result.output
        )


def test_bytecode_analyze_invalid():
    runner = CliRunner()
    with mock_context():
        result = runner.invoke(cli, ["analyze", "lolwut"])
        assert result.exit_code == 2
        assert FORMAT_ERROR in result.output
