import json
import os
from unittest.mock import patch

from click.testing import CliRunner

from mythx_cli.cli import cli

from .testdata import (
    ARTIFACT_DATA,
    INPUT_RESPONSE_OBJ,
    ISSUES_RESPONSE_OBJ,
    ISSUES_RESPONSE_SIMPLE,
    SUBMISSION_RESPONSE_OBJ,
)

EMPTY_PROJECT_ERROR = "Could not find any truffle artifacts. Are you in the project root? Did you run truffle compile?"


def test_truffle_analyze_async():
    runner = CliRunner()
    with patch("pythx.Client.analyze") as analyze_patch:
        analyze_patch.return_value = SUBMISSION_RESPONSE_OBJ
        with runner.isolated_filesystem():
            # create truffle-config.js
            with open("truffle-config.js", "w+") as conf_f:
                # we just need the file to be present
                conf_f.write("Truffle config stuff")

            # create build/contracts/ JSON files
            os.makedirs("build/contracts")
            with open("build/contracts/foo.json", "w+") as artifact_f:
                json.dump(ARTIFACT_DATA, artifact_f)

            result = runner.invoke(cli, ["analyze", "--async"])
            assert result.exit_code == 0
            assert SUBMISSION_RESPONSE_OBJ.analysis.uuid in result.output


def test_truffle_analyze_blocking():
    runner = CliRunner()
    with patch("pythx.Client.analyze") as analyze_patch, patch(
        "pythx.Client.analysis_ready"
    ) as ready_patch, patch("pythx.Client.report") as report_patch, patch(
        "pythx.Client.request_by_uuid"
    ) as input_patch:
        analyze_patch.return_value = SUBMISSION_RESPONSE_OBJ
        ready_patch.return_value = True
        report_patch.return_value = ISSUES_RESPONSE_OBJ
        input_patch.return_value = INPUT_RESPONSE_OBJ

        with runner.isolated_filesystem():
            # create truffle-config.js
            with open("truffle-config.js", "w+") as conf_f:
                # we just need the file to be present
                conf_f.write("Truffle config stuff")

            # create build/contracts/ JSON files
            os.makedirs("build/contracts")
            with open("build/contracts/foo.json", "w+") as artifact_f:
                json.dump(ARTIFACT_DATA, artifact_f)

            result = runner.invoke(cli, ["analyze"])
            assert result.exit_code == 0
            assert result.output == ISSUES_RESPONSE_SIMPLE


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
