import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest
import requests
from click.testing import CliRunner
from requests import RequestException

from mythx_cli.cli import cli
from mythx_cli.fuzz.exceptions import RequestError
from mythx_cli.fuzz.faas import FaasClient
from mythx_cli.fuzz.rpc import RPCClient

from .common import get_test_case

HARDHAT_ARTIFACT = get_test_case("testdata/hardhat-artifact.json")
HARDHAT_BUILD_INFO_ARTIFACT = get_test_case("testdata/hardhat-build-info-artifact.json")
GANACHE_URL = "http://localhost:9898"
FAAS_URL = "http://localhost:9899"


@pytest.fixture()
def hardhat_project(tmp_path, switch_dir=False):
    # switch to temp dir if requested
    if switch_dir:
        os.chdir(str(tmp_path))

    # add hardhat project structure
    os.makedirs(str(tmp_path / "artifacts/contracts/MasterChefV2.sol/"))
    os.makedirs(str(tmp_path / "artifacts/build-info/"))
    os.makedirs(str(tmp_path / "contracts"))

    # add sample brownie artifact
    with open(
        tmp_path / "artifacts/build-info/b78e6e91d6666dbbf407d4a383cd8177.json", "w+"
    ) as artifact_f:
        json.dump(HARDHAT_BUILD_INFO_ARTIFACT, artifact_f)

    with open("./hardhat.config.ts", "w+") as config_f:
        json.dump("sample", config_f)

    for filename, content in HARDHAT_ARTIFACT.items():
        with open(
            tmp_path / f"artifacts/contracts/MasterChefV2.sol/{filename}.json", "w+"
        ) as sol_f:
            json.dump(content, sol_f)

    with open(tmp_path / "contracts/MasterChefV2.sol", "w+") as sol_f:
        sol_f.write("sol code here")

        with open(tmp_path / "contracts/sample.sol", "w+") as sol_f:
            sol_f.write("sol code here")

    yield None

    os.remove(Path("./hardhat.config.ts").absolute())


def generate_config_file(base_path="", not_include=[]):
    config_file = "fuzz:"

    if "deployed_contract_address" not in not_include:
        config_file += '\n  deployed_contract_address: "0x7277646075fa72737e1F6114654C5d9949a67dF2"'
    if "number_of_cores" not in not_include:
        config_file += "\n  number_of_cores: 1"
    if "campaign_name_prefix" not in not_include:
        config_file += '\n  campaign_name_prefix: "hardhat_test"'
    if "rpc_url" not in not_include:
        config_file += f'\n  rpc_url: "{GANACHE_URL}"'
    if "faas_url" not in not_include:
        config_file += f'\n  faas_url: "{FAAS_URL}"'
    if "build_directory" not in not_include:
        config_file += f"\n  build_directory: {base_path}/artifacts"
    if "targets" not in not_include:
        config_file += f'\n  targets:\n    - "{base_path}/contracts/MasterChefV2.sol"'
    return config_file


def test_fuzz_no_build_dir(tmp_path):
    runner = CliRunner()
    with open(".mythx.yml", "w+") as conf_f:
        conf_f.write(generate_config_file(not_include=["build_directory"]))

    result = runner.invoke(cli, ["fuzz", "run", "contracts"])
    assert "Error: build_directory not found on .mythx.yml config file" in result.output
    assert result.exit_code != 0


def test_fuzz_no_deployed_address(tmp_path):
    runner = CliRunner()
    with open(".mythx.yml", "w+") as conf_f:
        conf_f.write(generate_config_file(not_include=["deployed_contract_address"]))

    result = runner.invoke(cli, ["fuzz", "run", "contracts"])
    assert (
        "Error: deployed_contract_address not found on .mythx.yml config file."
        in result.output
    )
    assert result.exit_code != 0


def test_fuzz_no_target(tmp_path):
    runner = CliRunner()
    with open(".mythx.yml", "w+") as conf_f:
        conf_f.write(generate_config_file(not_include=["targets"]))

    result = runner.invoke(cli, ["fuzz", "run"])
    assert "Error: Target not provided." in result.output
    assert result.exit_code != 0


def test_fuzz_no_contract_at_address(tmp_path, hardhat_project):
    with open(".mythx.yml", "w+") as conf_f:
        conf_f.write(generate_config_file(base_path=tmp_path))

    with patch.object(
        RPCClient, "contract_exists"
    ) as contract_exists_mock, patch.object(
        RPCClient, "get_all_blocks"
    ) as get_all_blocks_mock:
        get_all_blocks_mock.return_value = get_test_case(
            "testdata/ganache-all-blocks.json"
        )
        contract_exists_mock.return_value = False

        runner = CliRunner()
        result = runner.invoke(cli, ["fuzz", "run", f"{tmp_path}/contracts"])

    assert "Error: Unable to find a contract deployed" in result.output
    assert result.exit_code != 0


def test_faas_not_running(tmp_path, hardhat_project):
    with open(".mythx.yml", "w+") as conf_f:
        conf_f.write(generate_config_file(base_path=tmp_path))

    with patch.object(
        RPCClient, "contract_exists"
    ) as contract_exists_mock, patch.object(
        RPCClient, "get_all_blocks"
    ) as get_all_blocks_mock, patch.object(
        FaasClient, "start_faas_campaign"
    ) as start_faas_campaign_mock:
        get_all_blocks_mock.return_value = get_test_case(
            "testdata/ganache-all-blocks.json"
        )
        contract_exists_mock.return_value = True
        start_faas_campaign_mock.side_effect = RequestError(
            f"Error starting FaaS campaign."
        )

        runner = CliRunner()
        result = runner.invoke(
            cli, ["fuzz", "run", f"{tmp_path}/contracts/MasterChefV2.sol"]
        )

    assert (
        "Error: Unable to submit the campaign to the faas. Are you sure the service is running on"
        in result.output
    )
    assert result.exit_code != 0


def test_faas_target_config_file(tmp_path, hardhat_project):
    """Here we reuse the test_faas_not_running logic to check that the target is being read
    from the config file. This is possible because the faas not running error is triggered
    after the Target check. If the target was not available, a different error would be thrown
    and the test would fail"""
    with open(".mythx.yml", "w+") as conf_f:
        conf_f.write(generate_config_file(base_path=tmp_path))

    with patch.object(
        RPCClient, "contract_exists"
    ) as contract_exists_mock, patch.object(
        RPCClient, "get_all_blocks"
    ) as get_all_blocks_mock, patch.object(
        FaasClient, "start_faas_campaign"
    ) as start_faas_campaign_mock:
        get_all_blocks_mock.return_value = get_test_case(
            "testdata/ganache-all-blocks.json"
        )
        contract_exists_mock.return_value = True
        start_faas_campaign_mock.side_effect = RequestError(
            f"Error starting FaaS campaign."
        )

        runner = CliRunner()
        # we call the run command without the target parameter.
        result = runner.invoke(cli, ["fuzz", "run"])

    assert (
        "Error: Unable to submit the campaign to the faas. Are you sure the service is running on"
        in result.output
    )
    assert result.exit_code != 0


def test_rpc_not_running(tmp_path):
    with open(".mythx.yml", "w+") as conf_f:
        conf_f.write(generate_config_file(base_path=tmp_path))

    with patch.object(requests, "request") as requests_mock:
        requests_mock.side_effect = RequestException()

        runner = CliRunner()
        result = runner.invoke(
            cli, ["fuzz", "run", f"{tmp_path}/contracts/MasterChefV2.sol"]
        )

    assert "HTTP error calling RPC method eth_getCode with parameters" in result.output
    assert result.exit_code != 0


def test_fuzz_run(tmp_path, hardhat_project):
    with open(".mythx.yml", "w+") as conf_f:
        conf_f.write(generate_config_file(base_path=tmp_path))

    with patch.object(
        RPCClient, "contract_exists"
    ) as contract_exists_mock, patch.object(
        RPCClient, "get_all_blocks"
    ) as get_all_blocks_mock, patch.object(
        FaasClient, "start_faas_campaign"
    ) as start_faas_campaign_mock:
        get_all_blocks_mock.return_value = get_test_case(
            "testdata/ganache-all-blocks.json"
        )
        contract_exists_mock.return_value = True
        campaign_id = "560ba03a-8744-4da6-aeaa-a62568ccbf44"
        start_faas_campaign_mock.return_value = campaign_id

        runner = CliRunner()
        result = runner.invoke(
            cli, ["fuzz", "run", f"{tmp_path}/contracts/MasterChefV2.sol"]
        )

    contract_exists_mock.assert_called_with(
        "0x7277646075fa72737e1F6114654C5d9949a67dF2"
    )
    contract_exists_mock.assert_called_once()
    get_all_blocks_mock.assert_called_once()
    start_faas_campaign_mock.assert_called_once()
    called_with = start_faas_campaign_mock.call_args
    assert (
        f"You can view campaign here: {FAAS_URL}/campaigns/{campaign_id}"
        in result.output
    )

    request_payload = json.dumps(called_with[0])

    keywords = [
        "parameters",
        "name",
        "corpus",
        "sources",
        "contracts",
        "address-under-test",
        "source",
        "fileIndex",
        "sourcePaths",
        "deployedSourceMap",
        "mainSourceFile",
        "contractName",
        "bytecode",
        "deployedBytecode",
        "sourceMap",
        "deployedSourceMap",
    ]

    for keyword in keywords:
        assert keyword in request_payload

    assert result.exit_code == 0


def test_fuzz_run_corpus_target(tmp_path, hardhat_project):
    with open(".mythx.yml", "w+") as conf_f:
        conf_f.write(generate_config_file(base_path=tmp_path))

    with patch.object(
        RPCClient, "contract_exists"
    ) as contract_exists_mock, patch.object(
        RPCClient, "get_all_blocks"
    ) as get_all_blocks_mock, patch.object(
        FaasClient, "start_faas_campaign"
    ) as start_faas_campaign_mock:
        get_all_blocks_mock.return_value = get_test_case(
            "testdata/ganache-all-blocks.json"
        )
        contract_exists_mock.return_value = True
        campaign_id = "560ba03a-8744-4da6-aeaa-a62568ccbf44"
        start_faas_campaign_mock.return_value = campaign_id

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "fuzz",
                "run",
                f"{tmp_path}/contracts/MasterChefV2.sol",
                "-c",
                "prj_639cffb2a3e0407fbe2c701caaf5ab33",
            ],
        )

    contract_exists_mock.assert_not_called()
    get_all_blocks_mock.assert_not_called()
    start_faas_campaign_mock.assert_called_once()
    called_with = start_faas_campaign_mock.call_args
    assert (
        f"You can view campaign here: {FAAS_URL}/campaigns/{campaign_id}"
        in result.output
    )

    assert called_with[0][0]["corpus"] == {
        "target": "prj_639cffb2a3e0407fbe2c701caaf5ab33"
    }

    assert result.exit_code == 0


@pytest.mark.parametrize("keyword", ("run", "disarm", "arm", "run"))
def test_fuzz_subcommands_present(keyword):
    runner = CliRunner()

    result = runner.invoke(cli, ["fuzz", "--help"])

    assert keyword in result.output


@patch("mythx_cli.analyze.scribble.ScribbleMixin.instrument_solc_in_place")
def test_fuzz_arm(mock, tmp_path, hardhat_project):
    runner = CliRunner()
    result = runner.invoke(cli, ["fuzz", "arm", f"{tmp_path}/contracts/sample.sol"])

    mock.assert_called()
    mock.assert_called_with(
        file_list=(f"{tmp_path}/contracts/sample.sol",),
        scribble_path="scribble",
        remappings=[],
        solc_version=None,
    )
    assert result.exit_code == 0


@patch("mythx_cli.analyze.scribble.ScribbleMixin.disarm_solc_in_place")
def test_fuzz_disarm(mock, tmp_path, hardhat_project):
    runner = CliRunner()
    result = runner.invoke(cli, ["fuzz", "disarm", f"{tmp_path}/contracts/sample.sol"])

    mock.assert_called()
    mock.assert_called_with(
        file_list=(f"{tmp_path}/contracts/sample.sol",),
        scribble_path="scribble",
        remappings=[],
        solc_version=None,
    )
    assert result.exit_code == 0
