import json
import os
from copy import deepcopy

import pytest
from click.testing import CliRunner
from mythx_models.response import (
    AnalysisInputResponse,
    AnalysisSubmissionResponse,
    DetectedIssuesResponse,
    Severity,
)

from mythx_cli.cli import cli

from .common import get_test_case, mock_context

FORMAT_ERROR = (
    "Could not interpret argument lolwut as bytecode, Solidity file, or Truffle project"
)
SUBMISSION_RESPONSE = get_test_case(
    "testdata/analysis-submission-response.json", AnalysisSubmissionResponse
)
ISSUES_RESPONSE = get_test_case(
    "testdata/detected-issues-response.json", DetectedIssuesResponse
)
INPUT_RESPONSE = get_test_case(
    "testdata/analysis-input-response.json", AnalysisInputResponse
)
ISSUES_TABLE = get_test_case("testdata/detected-issues-table.txt", raw=True)
SOLIDITY_CODE = """pragma solidity 0.4.13;

contract OutdatedCompilerVersion {
    uint public x = 1;
}
"""
VERSION_ERROR = (
    "Error: Error installing solc version v9001: Invalid version string: '9001'"
)
PRAGMA_ERROR = "No pragma found - please specify a solc version with --solc-version"
EMPTY_PROJECT_ERROR = "Could not find any truffle artifacts. Are you in the project root? Did you run truffle compile?"
TRUFFLE_ARTIFACT = get_test_case("testdata/truffle-artifact.json")


def setup_solidity_test():
    with open("outdated.sol", "w+") as conf_f:
        conf_f.write(SOLIDITY_CODE)


def setup_truffle_test():
    with open("truffle-config.js", "w+") as conf_f:
        conf_f.write("Truffle config stuff")

    os.makedirs("build/contracts")
    with open("build/contracts/foo.json", "w+") as artifact_f:
        json.dump(TRUFFLE_ARTIFACT, artifact_f)


@pytest.mark.parametrize(
    "mode,params,value,contained,retval",
    (
        pytest.param(
            "bytecode",
            ["--output", "test.log", "analyze", "0xfe"],
            INPUT_RESPONSE.source_list[0],
            True,
            0,
            id="bytecode output file",
        ),
        pytest.param(
            "bytecode",
            ["analyze", "0xfe"],
            INPUT_RESPONSE.source_list[0],
            True,
            0,
            id="bytecode analyze param",
        ),
        pytest.param(
            "bytecode",
            ["analyze", "--create-group", "0xfe"],
            INPUT_RESPONSE.source_list[0],
            True,
            0,
            id="bytecode create group",
        ),
        pytest.param(
            "bytecode",
            ["analyze", "--swc-blacklist", "SWC-110", "0xfe"],
            INPUT_RESPONSE.source_list[0],
            False,
            0,
            id="bytecode blacklist 110",
        ),
        pytest.param(
            "bytecode",
            ["analyze", "--min-severity", "high", "0xfe"],
            INPUT_RESPONSE.source_list[0],
            False,
            0,
            id="bytecode high sev filter",
        ),
        pytest.param(
            "bytecode",
            ["analyze", "lolwut"],
            FORMAT_ERROR,
            True,
            2,
            id="bytecode invalid analyze",
        ),
        pytest.param(
            "solidity",
            ["analyze", "--async"],
            SUBMISSION_RESPONSE.analysis.uuid,
            True,
            0,
            id="solidity analyze async",
        ),
        pytest.param(
            "solidity",
            ["analyze"],
            ISSUES_TABLE,
            True,
            0,
            id="solidity issue table no params",
        ),
        pytest.param(
            "solidity",
            ["analyze", "--swc-blacklist", "SWC-110"],
            INPUT_RESPONSE.source_list[0],
            False,
            0,
            id="solidity blacklist 110",
        ),
        pytest.param(
            "solidity",
            ["analyze", "--min-severity", "high"],
            INPUT_RESPONSE.source_list[0],
            False,
            0,
            id="solidity high sev filter",
        ),
        pytest.param(
            "solidity",
            ["analyze", "outdated.sol"],
            ISSUES_TABLE,
            True,
            0,
            id="solidity issue table file param",
        ),
        pytest.param(
            "solidity",
            ["analyze", "--create-group", "outdated.sol"],
            ISSUES_TABLE,
            True,
            0,
            id="solidity create group",
        ),
        pytest.param(
            "solidity", ["analyze", "."], ISSUES_TABLE, True, 0, id="solidity cwd"
        ),
        pytest.param(
            "solidity",
            ["--output", "test.log", "analyze", "outdated.sol"],
            ISSUES_TABLE,
            True,
            0,
            id="solidity output file",
        ),
        pytest.param(
            "solidity",
            ["analyze", "--include", "invalid"],
            INPUT_RESPONSE.source_list[0],
            False,
            2,
            id="solidity invalid include",
        ),
        pytest.param(
            "solidity",
            ["analyze", "--solc-version", "9001", "outdated.sol"],
            VERSION_ERROR,
            True,
            2,
            id="solidity invalid solc version",
        ),
        pytest.param(
            "truffle",
            ["analyze", "--async"],
            SUBMISSION_RESPONSE.analysis.uuid,
            True,
            0,
            id="truffle async",
        ),
        pytest.param(
            "truffle",
            ["--output", "test.log", "analyze"],
            ISSUES_TABLE,
            True,
            0,
            id="truffle output file",
        ),
        pytest.param(
            "truffle", ["analyze"], ISSUES_TABLE, True, 0, id="truffle issue table"
        ),
        pytest.param(
            "truffle",
            ["analyze", "--create-group"],
            ISSUES_TABLE,
            True,
            0,
            id="truffle create group",
        ),
        pytest.param(
            "truffle",
            ["analyze", "--include", "invalid"],
            INPUT_RESPONSE.source_list[0],
            False,
            2,
            id="truffle invalid include",
        ),
        pytest.param(
            "truffle",
            ["analyze", "--swc-blacklist", "SWC-110"],
            INPUT_RESPONSE.source_list[0],
            False,
            0,
            id="truffle blacklist 110",
        ),
        pytest.param(
            "truffle",
            ["analyze", "--min-severity", "high"],
            INPUT_RESPONSE.source_list[0],
            False,
            0,
            id="truffle high sev filter",
        ),
    ),
)
def test_bytecode_analyze(mode, params, value, contained, retval):
    runner = CliRunner()
    with mock_context(), runner.isolated_filesystem():
        if mode == "solidity":
            setup_solidity_test()
        elif mode == "truffle":
            setup_truffle_test()
        result = runner.invoke(cli, params, input="y\n")

        if "--output" in params:
            with open("test.log") as f:
                output = f.read()
        else:
            output = result.output

        if contained:
            assert value in output
        else:
            assert value not in output

        assert result.exit_code == retval


def test_exit_on_missing_consent():
    runner = CliRunner()
    with mock_context(), runner.isolated_filesystem():
        setup_solidity_test()
        result = runner.invoke(cli, ["analyze"], input="n\n")

        assert (
            result.output
            == "Found 1 Solidity file(s) before filtering. Continue? [y/N]: n\n"
        )
        assert result.exit_code == 0


def test_bytecode_analyze_ci():
    runner = CliRunner()
    with mock_context() as patches:
        # set up high-severity issue
        issues_resp = deepcopy(ISSUES_RESPONSE)
        issues_resp.issue_reports[0].issues[0].severity = Severity.HIGH
        patches[2].return_value = issues_resp

        result = runner.invoke(cli, ["--ci", "analyze", "0xfe"])

        assert INPUT_RESPONSE.source_list[0] in result.output
        assert result.exit_code == 1


def test_bytecode_analyze_invalid():
    runner = CliRunner()
    with mock_context():
        result = runner.invoke(cli, ["analyze", "lolwut"])

        assert FORMAT_ERROR in result.output
        assert result.exit_code == 2


def test_solidity_analyze_blocking_ci():
    runner = CliRunner()
    with mock_context() as patches:
        # set up high-severity issue
        issues_resp = deepcopy(ISSUES_RESPONSE)
        issues_resp.issue_reports[0].issues[0].severity = Severity.HIGH
        patches[2].return_value = issues_resp

        with runner.isolated_filesystem():
            # initialize sample solidity file
            with open("outdated.sol", "w+") as conf_f:
                conf_f.write(SOLIDITY_CODE)

            result = runner.invoke(cli, ["--ci", "analyze"], input="y\n")

            assert "Assert Violation" in result.output
            assert INPUT_RESPONSE.source_list[0] in result.output
            assert result.exit_code == 1


def test_solidity_analyze_multiple_with_group():
    runner = CliRunner()
    with mock_context(), runner.isolated_filesystem():
        # initialize sample solidity file
        with open("outdated.sol", "w+") as conf_f:
            conf_f.write(SOLIDITY_CODE)

        with open("outdated2.sol", "w+") as conf_f:
            conf_f.write(SOLIDITY_CODE)

        result = runner.invoke(
            cli,
            ["--debug", "analyze", "--create-group", "outdated.sol", "outdated2.sol"],
        )
        assert result.output == ISSUES_TABLE + ISSUES_TABLE
        assert result.exit_code == 0


def test_solidity_analyze_multiple_with_config_group():
    runner = CliRunner()
    with mock_context(), runner.isolated_filesystem():
        # initialize sample solidity file
        with open("outdated.sol", "w+") as conf_f:
            conf_f.write(SOLIDITY_CODE)

        with open("outdated2.sol", "w+") as conf_f:
            conf_f.write(SOLIDITY_CODE)

        with open(".mythx.yml", "w+") as conf_f:
            conf_f.write("analyze:\n  create-group: true\n")

        result = runner.invoke(
            cli, ["--debug", "analyze", "outdated.sol", "outdated2.sol"]
        )
        assert result.output == ISSUES_TABLE + ISSUES_TABLE
        assert result.exit_code == 0


def test_solidity_analyze_recursive_blacklist():
    runner = CliRunner()
    with mock_context(), runner.isolated_filesystem():
        # initialize sample solidity file
        with open("outdated.sol", "w+") as conf_f:
            conf_f.write(SOLIDITY_CODE)

        os.mkdir("./node_modules")
        with open("./node_modules/outdated2.sol", "w+") as conf_f:
            # should be ignored
            conf_f.write(SOLIDITY_CODE)

        result = runner.invoke(
            cli, ["--debug", "--yes", "analyze", "--create-group", "."]
        )
        assert result.output == ISSUES_TABLE
        assert result.exit_code == 0


def test_solidity_analyze_missing_version():
    runner = CliRunner()
    with mock_context(), runner.isolated_filesystem():
        # initialize sample solidity file without pragma line
        with open("outdated.sol", "w+") as conf_f:
            conf_f.writelines(SOLIDITY_CODE.split("\n")[1:])

        result = runner.invoke(cli, ["analyze", "outdated.sol"])

        assert PRAGMA_ERROR in result.output
        assert result.exit_code == 2


def test_solidity_analyze_user_solc_version():
    runner = CliRunner()
    with mock_context(), runner.isolated_filesystem():
        # initialize sample solidity file without pragma line
        with open("outdated.sol", "w+") as conf_f:
            conf_f.writelines(SOLIDITY_CODE.split("\n")[1:])

        result = runner.invoke(
            cli, ["analyze", "--solc-version", "0.4.13", "outdated.sol"]
        )

        assert result.output == ISSUES_TABLE
        assert result.exit_code == 0


def test_solidity_analyze_config_solc_version():
    runner = CliRunner()
    with mock_context(), runner.isolated_filesystem():
        # initialize sample solidity file without pragma line
        with open("outdated.sol", "w+") as conf_f:
            conf_f.writelines(SOLIDITY_CODE.split("\n")[1:])

        with open(".mythx.yml", "w+") as conf_f:
            conf_f.write("analyze:\n  solc: 0.4.13\n")

        result = runner.invoke(cli, ["analyze", "outdated.sol"])

        assert result.output == ISSUES_TABLE
        assert result.exit_code == 0


def test_truffle_analyze_blocking_ci():
    runner = CliRunner()
    with mock_context() as patches, runner.isolated_filesystem():
        # set up high-severity issue
        issues_resp = deepcopy(ISSUES_RESPONSE)
        issues_resp.issue_reports[0].issues[0].severity = Severity.HIGH
        patches[2].return_value = issues_resp

        # create truffle-config.js
        with open("truffle-config.js", "w+") as conf_f:
            # we just need the file to be present
            conf_f.write("Truffle config stuff")

        # create build/contracts/ JSON files
        os.makedirs("build/contracts")
        with open("build/contracts/foo.json", "w+") as artifact_f:
            json.dump(TRUFFLE_ARTIFACT, artifact_f)

        result = runner.invoke(cli, ["--debug", "--ci", "analyze"])

        assert "Assert Violation" in result.output
        assert INPUT_RESPONSE.source_list[0] in result.output
        assert result.exit_code == 1


def test_truffle_analyze_no_files():
    runner = CliRunner()

    with runner.isolated_filesystem():
        # create truffle-config.js
        with open("truffle-config.js", "w+") as conf_f:
            # we just need the file to be present
            conf_f.write("Truffle config stuff")

            result = runner.invoke(cli, ["analyze"])

            assert EMPTY_PROJECT_ERROR in result.output
            assert result.exit_code == 2


def test_truffle_analyze_blocking_config_ci():
    runner = CliRunner()
    with mock_context() as patches, runner.isolated_filesystem():
        # set up high-severity issue
        issues_resp = deepcopy(ISSUES_RESPONSE)
        issues_resp.issue_reports[0].issues[0].severity = Severity.HIGH
        patches[2].return_value = issues_resp

        # create truffle-config.js
        with open("truffle-config.js", "w+") as conf_f:
            # we just need the file to be present
            conf_f.write("Truffle config stuff")

        with open(".mythx.yml", "w+") as conf_f:
            conf_f.write("ci: true\n")

        # create build/contracts/ JSON files
        os.makedirs("build/contracts")
        with open("build/contracts/foo.json", "w+") as artifact_f:
            json.dump(TRUFFLE_ARTIFACT, artifact_f)

        result = runner.invoke(cli, ["--debug", "analyze"])

        assert "Assert Violation" in result.output
        assert INPUT_RESPONSE.source_list[0] in result.output
        assert result.exit_code == 1
