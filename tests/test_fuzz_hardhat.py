import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from mythx_cli.cli import cli
from mythx_cli.fuzz.faas import FaasClient
from mythx_cli.fuzz.rpc import RPCClient

from .common import get_test_case

HARDHAT_ARTIFACT = get_test_case("testdata/hardhat-artifact.json")
HARDHAT_BUILD_INFO_ARTIFACT = get_test_case("testdata/hardhat-build-info-artifact.json")
GANACHE_URL = "http://localhost:9898"
FAAS_URL = "http://localhost:9899"

INSTRUMENTED_SOL_CODE = "sol code here"
ORIGINAL_SOL_CODE = "original sol code here"


@pytest.fixture()
def hardhat_project(tmp_path, request):
    # switch to temp dir if requested
    if hasattr(request, "param") and request.param:
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
        sol_f.write(INSTRUMENTED_SOL_CODE)

    with open(tmp_path / "contracts/sample.sol", "w+") as sol_f:
        sol_f.write(INSTRUMENTED_SOL_CODE)

    with open(tmp_path / "contracts/MasterChefV2.sol.original", "w+") as sol_f:
        sol_f.write(ORIGINAL_SOL_CODE)

    with open(tmp_path / "contracts/sample.sol.original", "w+") as sol_f:
        sol_f.write(ORIGINAL_SOL_CODE)

    yield {"switch_dir": hasattr(request, "param") and request.param}

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


@pytest.mark.parametrize("absolute_target", [True, False])
@pytest.mark.parametrize("hardhat_project", [False, True], indirect=True)
def test_fuzz_run(tmp_path, hardhat_project, absolute_target):
    if not absolute_target and not hardhat_project["switch_dir"]:
        pytest.skip(
            "absolute_target=False, hardhat_project=False through parametrization"
        )

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
        target = (
            f"{tmp_path}/contracts/MasterChefV2.sol"
            if absolute_target
            else "contracts/MasterChefV2.sol"
        )
        result = runner.invoke(cli, ["fuzz", "run", target])

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
