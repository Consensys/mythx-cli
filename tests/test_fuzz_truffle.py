import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from mythx_cli.cli import cli
from mythx_cli.fuzz.faas import FaasClient
from mythx_cli.fuzz.ide.truffle import TruffleArtifacts
from mythx_cli.fuzz.rpc import RPCClient

from .common import get_test_case

TRUFFLE_ARTIFACT = get_test_case("testdata/truffle-artifact.json")
GANACHE_URL = "http://localhost:9898"
FAAS_URL = "http://localhost:9899"


@pytest.fixture()
def truffle_project(tmp_path, request):
    # switch to temp dir if requested
    if hasattr(request, "param") and request.param:
        os.chdir(str(tmp_path))

    # add truffle project structure
    os.makedirs(str(tmp_path / "build/contracts/MasterChefV2.sol/"))
    os.makedirs(str(tmp_path / "contracts"))

    with open("./truffle-config.js", "w+") as config_f:
        json.dump("sample", config_f)

    TRUFFLE_ARTIFACT["contractName"] = f"Foo"
    TRUFFLE_ARTIFACT["sourcePath"] = f"{tmp_path}/contracts/sample.sol"

    # add sample brownie artifact
    with open(tmp_path / "build/contracts/Foo.json", "w+") as artifact_f:
        json.dump(TRUFFLE_ARTIFACT, artifact_f)
    with open(tmp_path / "contracts/sample.sol", "w+") as sol_f:
        sol_f.write("sol code here")

    yield {"switch_dir": hasattr(request, "param") and request.param}
    os.remove(Path("./truffle-config.js").absolute())


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
        config_file += f"\n  build_directory: {base_path}/build"
    if "targets" not in not_include:
        config_file += f'\n  targets:\n    - "{base_path}/contracts/MasterChefV2.sol"'
    return config_file


@pytest.mark.parametrize("absolute_target", [True, False])
@pytest.mark.parametrize("truffle_project", [False, True], indirect=True)
def test_fuzz_run(tmp_path, truffle_project, absolute_target):
    if not absolute_target and not truffle_project["switch_dir"]:
        pytest.skip(
            "absolute_target=False, truffle_project=False through parametrization"
        )

    with open(".mythx.yml", "w+") as conf_f:
        conf_f.write(generate_config_file(base_path=tmp_path))

    with patch.object(
        RPCClient, "contract_exists"
    ) as contract_exists_mock, patch.object(
        RPCClient, "get_all_blocks"
    ) as get_all_blocks_mock, patch.object(
        FaasClient, "start_faas_campaign"
    ) as start_faas_campaign_mock, patch.object(
        TruffleArtifacts, "query_truffle_db"
    ) as query_truffle_db_mock:
        get_all_blocks_mock.return_value = get_test_case(
            "testdata/ganache-all-blocks.json"
        )
        contract_exists_mock.return_value = True
        campaign_id = "560ba03a-8744-4da6-aeaa-a62568ccbf44"
        start_faas_campaign_mock.return_value = campaign_id

        query_truffle_db_mock.side_effect = [
            {"projectId": "test-project"},
            {
                "project": {
                    "contracts": [
                        {
                            "name": "Foo",
                            "compilation": {
                                "processedSources": [
                                    {
                                        "source": {
                                            "sourcePath": f"{tmp_path}/contracts/sample.sol"
                                        }
                                    }
                                ]
                            },
                        }
                    ]
                }
            },
        ]

        runner = CliRunner()
        target = (
            f"{tmp_path}/contracts/sample.sol"
            if absolute_target
            else "contracts/sample.sol"
        )
        cwd = os.getcwd()
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


def test_fuzz_run_corpus_target(tmp_path, truffle_project):
    with open(".mythx.yml", "w+") as conf_f:
        conf_f.write(generate_config_file(base_path=tmp_path))

    with patch.object(
        RPCClient, "contract_exists"
    ) as contract_exists_mock, patch.object(
        RPCClient, "get_all_blocks"
    ) as get_all_blocks_mock, patch.object(
        FaasClient, "start_faas_campaign"
    ) as start_faas_campaign_mock, patch.object(
        TruffleArtifacts, "query_truffle_db"
    ) as query_truffle_db_mock:
        get_all_blocks_mock.return_value = get_test_case(
            "testdata/ganache-all-blocks.json"
        )
        contract_exists_mock.return_value = True
        campaign_id = "560ba03a-8744-4da6-aeaa-a62568ccbf44"
        start_faas_campaign_mock.return_value = campaign_id

        query_truffle_db_mock.side_effect = [
            {"projectId": "test-project"},
            {
                "project": {
                    "contracts": [
                        {
                            "name": "Foo",
                            "compilation": {
                                "processedSources": [
                                    {
                                        "source": {
                                            "sourcePath": f"{tmp_path}/contracts/sample.sol"
                                        }
                                    }
                                ]
                            },
                        }
                    ]
                }
            },
        ]

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "fuzz",
                "run",
                f"{tmp_path}/contracts/sample.sol",
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
