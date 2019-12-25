import json
import os
from copy import deepcopy
from unittest.mock import patch

from click.testing import CliRunner

from mythx_cli.cli import cli
from mythx_models.response import (
    AnalysisInputResponse,
    AnalysisSubmissionResponse,
    DetectedIssuesResponse,
    Severity,
)

from .common import get_test_case

TRUFFLE_ARTIFACT = get_test_case("testdata/truffle-artifact.json")
INPUT_RESPONSE = get_test_case(
    "testdata/analysis-input-response.json", AnalysisInputResponse
)
ISSUES_RESPONSE = get_test_case(
    "testdata/detected-issues-response.json", DetectedIssuesResponse
)
SUBMISSION_RESPONSE = get_test_case(
    "testdata/analysis-submission-response.json", AnalysisSubmissionResponse
)
ISSUES_TABLE = get_test_case("testdata/detected-issues-table.txt", raw=True)
EMPTY_PROJECT_ERROR = "Could not find any truffle artifacts. Are you in the project root? Did you run truffle compile?"


def test_truffle_analyze_async():
    runner = CliRunner()
    with patch("pythx.Client.analyze") as analyze_patch:
        analyze_patch.return_value = SUBMISSION_RESPONSE
        with runner.isolated_filesystem():
            # create truffle-config.js
            with open("truffle-config.js", "w+") as conf_f:
                # we just need the file to be present
                conf_f.write("Truffle config stuff")

            # create build/contracts/ JSON files
            os.makedirs("build/contracts")
            with open("build/contracts/foo.json", "w+") as artifact_f:
                json.dump(TRUFFLE_ARTIFACT, artifact_f)

            result = runner.invoke(cli, ["analyze", "--async"])
            assert result.exit_code == 0
            assert SUBMISSION_RESPONSE.analysis.uuid in result.output


def test_truffle_analyze_file_output():
    runner = CliRunner()
    with patch("pythx.Client.analyze") as analyze_patch, patch(
        "pythx.Client.analysis_ready"
    ) as ready_patch, patch("pythx.Client.report") as report_patch, patch(
        "pythx.Client.request_by_uuid"
    ) as input_patch:
        analyze_patch.return_value = SUBMISSION_RESPONSE
        ready_patch.return_value = True
        report_patch.return_value = deepcopy(ISSUES_RESPONSE)
        input_patch.return_value = INPUT_RESPONSE
        with runner.isolated_filesystem():
            # create truffle-config.js
            with open("truffle-config.js", "w+") as conf_f:
                # we just need the file to be present
                conf_f.write("Truffle config stuff")

            # create build/contracts/ JSON files
            os.makedirs("build/contracts")
            with open("build/contracts/foo.json", "w+") as artifact_f:
                json.dump(TRUFFLE_ARTIFACT, artifact_f)

            result = runner.invoke(cli, ["--output", "test.log", "analyze"])
            assert result.exit_code == 0
            with open("test.log") as f:
                assert f.read() == ISSUES_TABLE


def test_truffle_analyze_blocking():
    runner = CliRunner()
    with patch("pythx.Client.analyze") as analyze_patch, patch(
        "pythx.Client.analysis_ready"
    ) as ready_patch, patch("pythx.Client.report") as report_patch, patch(
        "pythx.Client.request_by_uuid"
    ) as input_patch:
        analyze_patch.return_value = SUBMISSION_RESPONSE
        ready_patch.return_value = True
        report_patch.return_value = deepcopy(ISSUES_RESPONSE)
        input_patch.return_value = INPUT_RESPONSE

        with runner.isolated_filesystem():
            # create truffle-config.js
            with open("truffle-config.js", "w+") as conf_f:
                # we just need the file to be present
                conf_f.write("Truffle config stuff")

            # create build/contracts/ JSON files
            os.makedirs("build/contracts")
            with open("build/contracts/foo.json", "w+") as artifact_f:
                json.dump(TRUFFLE_ARTIFACT, artifact_f)

            result = runner.invoke(cli, ["analyze"])
            assert result.exit_code == 0
            assert result.output == ISSUES_TABLE


def test_truffle_analyze_blocking_ci():
    runner = CliRunner()
    with patch("pythx.Client.analyze") as analyze_patch, patch(
        "pythx.Client.analysis_ready"
    ) as ready_patch, patch("pythx.Client.report") as report_patch, patch(
        "pythx.Client.request_by_uuid"
    ) as input_patch:
        # set up high-severity issue
        issues_resp = deepcopy(ISSUES_RESPONSE)
        issues_resp.issue_reports[0].issues[0].severity = Severity.HIGH

        analyze_patch.return_value = SUBMISSION_RESPONSE
        ready_patch.return_value = True
        report_patch.return_value = issues_resp
        input_patch.return_value = INPUT_RESPONSE

        with runner.isolated_filesystem():
            # create truffle-config.js
            with open("truffle-config.js", "w+") as conf_f:
                # we just need the file to be present
                conf_f.write("Truffle config stuff")

            # create build/contracts/ JSON files
            os.makedirs("build/contracts")
            with open("build/contracts/foo.json", "w+") as artifact_f:
                json.dump(TRUFFLE_ARTIFACT, artifact_f)

            result = runner.invoke(cli, ["--ci", "analyze"])
            assert result.exit_code == 1
            assert "Assert Violation" in result.output
            assert INPUT_RESPONSE.source_list[0] in result.output


def test_truffle_analyze_blocking_blacklist():
    runner = CliRunner()
    with patch("pythx.Client.analyze") as analyze_patch, patch(
        "pythx.Client.analysis_ready"
    ) as ready_patch, patch("pythx.Client.report") as report_patch, patch(
        "pythx.Client.request_by_uuid"
    ) as input_patch:
        analyze_patch.return_value = SUBMISSION_RESPONSE
        ready_patch.return_value = True
        report_patch.return_value = deepcopy(ISSUES_RESPONSE)
        input_patch.return_value = INPUT_RESPONSE

        with runner.isolated_filesystem():
            # create truffle-config.js
            with open("truffle-config.js", "w+") as conf_f:
                # we just need the file to be present
                conf_f.write("Truffle config stuff")

            # create build/contracts/ JSON files
            os.makedirs("build/contracts")
            with open("build/contracts/foo.json", "w+") as artifact_f:
                json.dump(TRUFFLE_ARTIFACT, artifact_f)

            result = runner.invoke(cli, ["analyze", "--swc-blacklist", "SWC-110"])
            assert result.exit_code == 0
            assert "Assert Violation" not in result.output
            assert (
                "/home/spoons/diligence/mythx-qa/land/contracts/estate/EstateStorage.sol"
                not in result.output
            )


def test_truffle_analyze_blocking_filter():
    runner = CliRunner()
    with patch("pythx.Client.analyze") as analyze_patch, patch(
        "pythx.Client.analysis_ready"
    ) as ready_patch, patch("pythx.Client.report") as report_patch, patch(
        "pythx.Client.request_by_uuid"
    ) as input_patch:
        analyze_patch.return_value = SUBMISSION_RESPONSE
        ready_patch.return_value = True
        report_patch.return_value = deepcopy(ISSUES_RESPONSE)
        input_patch.return_value = INPUT_RESPONSE

        with runner.isolated_filesystem():
            # create truffle-config.js
            with open("truffle-config.js", "w+") as conf_f:
                # we just need the file to be present
                conf_f.write("Truffle config stuff")

            # create build/contracts/ JSON files
            os.makedirs("build/contracts")
            with open("build/contracts/foo.json", "w+") as artifact_f:
                json.dump(TRUFFLE_ARTIFACT, artifact_f)

            result = runner.invoke(cli, ["analyze", "--min-severity", "high"])
            assert result.exit_code == 0
            assert "Assert Violation" not in result.output
            assert (
                "/home/spoons/diligence/mythx-qa/land/contracts/estate/EstateStorage.sol"
                not in result.output
            )


def test_truffle_analyze_no_files():
    runner = CliRunner()

    with runner.isolated_filesystem():
        # create truffle-config.js
        with open("truffle-config.js", "w+") as conf_f:
            # we just need the file to be present
            conf_f.write("Truffle config stuff")

            result = runner.invoke(cli, ["analyze"])
            assert result.exit_code == 2
            assert EMPTY_PROJECT_ERROR in result.output
