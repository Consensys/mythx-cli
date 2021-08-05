import logging
import os
import traceback
from enum import Enum
from pathlib import Path

import click

from mythx_cli.fuzz.ide.brownie import BrownieJob
from mythx_cli.fuzz.ide.hardhat import HardhatJob

from .exceptions import BadStatusCode, RPCCallError
from .faas import FaasClient
from .rpc import RPCClient

LOGGER = logging.getLogger("mythx-cli")

headers = {"Content-Type": "application/json"}

time_limit_seconds = 3000


class IDE(Enum):
    BROWNIE = "brownie"
    HARDHAT = "hardhat"
    TRUFFLE = "truffle"
    SOLIDITY = "solidity"


def determine_ide() -> IDE:
    root_dir = Path.cwd().absolute()
    files = list(os.walk(root_dir))[0][2]
    if "brownie-config.yaml" in files:
        return IDE.BROWNIE
    if "hardhat.config.ts" in files:
        return IDE.HARDHAT
    if "hardhat.config.js" in files:
        return IDE.HARDHAT
    if "truffle-config.js" in files:
        return IDE.TRUFFLE
    return IDE.SOLIDITY


@click.command("run")
@click.argument("target", default=None, nargs=-1, required=False)
@click.option(
    "-a", "--address", type=click.STRING, help="Address of the main contract to analyze"
)
@click.option(
    "-m",
    "--more-addresses",
    type=click.STRING,
    help="Addresses of other contracts to analyze, separated by commas",
)
@click.option(
    "-c",
    "--corpus-target",
    type=click.STRING,
    help="Project UUID, Campaign UUID or Corpus UUID to reuse the corpus from. "
         "In case of a project, corpus from the project's latest submitted campaign will be used",
    default=None,
    required=False,
)
@click.option(
    "-s",
    "--map-to-original-source",
    is_flag=True,
    default=False,
    help="Map the analyses results to the original source code, instead of the instrumented one. "
         "This is meant to be used with Scribble.",
)

@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Outputs the data to be sent to the FaaS API without making the request.",
)

@click.option(
    "-k",
    "--api-key",
    type=click.STRING,
    help="API key, can be created on the FaaS Dashboard. ",
    default=None,
    required=False,
)
@click.pass_obj
def fuzz_run(ctx, address, more_addresses, corpus_target, map_to_original_source, dry_run, api_key, target):
    # read YAML config params from ctx dict, e.g. ganache rpc url
    #   Introduce a separate `fuzz` section in the YAML file

    # construct seed state from ganache

    # construct the FaaS campaign object
    #   helpful method: mythx_cli/analyze/solidity.py:SolidityJob.generate_payloads
    #   NOTE: This currently patches link placeholders in the creation
    #         bytecode with the zero address. If we need to submit bytecode from
    #         solc compilation, we need to find a way to replace these with the Ganache
    #         instance's addresses. Preferably we pull all of this data from Ganache
    #         itself and just enrich the payload with source and AST data from the
    #         SolidityJob payload list

    # submit the FaaS payload, do error handling

    # print FaaS dashboard url pointing to campaign
    analyze_config = ctx.get("fuzz")

    default_config = {
        "rpc_url": "http://localhost:7545",
        "faas_url": "http://localhost:8080",
        "harvey_num_cores": 2,
        "campaign_name_prefix": "untitled",
        "map_to_original_source": False,
    }
    config_options = analyze_config.keys()
    # Mandatory config parameters verification
    if "build_directory" not in config_options:
        raise click.exceptions.UsageError(
            "build_directory not found on .mythx.yml config file"
            "\nYou need to provide your project's build directory in the .mythx.yml config file"
        )
    if "deployed_contract_address" not in config_options:
        raise click.exceptions.UsageError(
            "deployed_contract_address not found on .mythx.yml config file."
            "\nYou need to provide the address where your main contract is deployed on the .mythx.yml"
        )
    if not target and "targets" not in config_options:
        raise click.exceptions.UsageError(
            "Target not provided. You need to provide a target as the last parameter of the fuzz run command."
            "\nYou can also set the target on the `fuzz` key of your .mythx.yml config file."
            "\nSee https://mythx-cli.readthedocs.io/en/latest/advanced-usage.html#configuration-using-mythx-yml"
            " for more information."
        )
    if not target:
        target = analyze_config["targets"]
    if not map_to_original_source:
        map_to_original_source = (
            analyze_config["map_to_original_source"]
            if "map_to_original_source" in config_options
            else default_config["map_to_original_source"]
        )
    if not api_key:
        api_key = (
            analyze_config["api_key"]
            if "api_key" in config_options
            else None
        )
    # Optional config parameters
    # Here we parse the config parameters from the config file and use defaults for non available values
    contract_address = analyze_config["deployed_contract_address"]
    rpc_url = (
        analyze_config["rpc_url"]
        if "rpc_url" in config_options
        else default_config["rpc_url"]
    )
    faas_url = (
        analyze_config["faas_url"]
        if "faas_url" in config_options
        else default_config["faas_url"]
    )
    number_of_cores = (
        analyze_config["number_of_cores"]
        if "number_of_cores" in config_options
        else default_config["harvey_num_cores"]
    )
    campaign_name_prefix = (
        analyze_config["campaign_name_prefix"]
        if "campaign_name_prefix" in config_options
        else default_config["campaign_name_prefix"]
    )

    if more_addresses is None:
        other_addresses = []
    else:
        other_addresses = more_addresses.split(",")

    _corpus_target = corpus_target or analyze_config.get("corpus_target", None)

    rpc_client = RPCClient(rpc_url, number_of_cores)
    if not _corpus_target:
        try:
            contract_code_response = rpc_client.contract_exists(contract_address)
        except RPCCallError as e:
            raise click.exceptions.UsageError(f"RPC endpoint." f"\n{e}")

        if not contract_code_response:
            LOGGER.warning(f"Contract code not found")
            raise click.exceptions.ClickException(
                f"Unable to find a contract deployed at {contract_address}."
            )
    seed_state = rpc_client.get_seed_state(
        contract_address, other_addresses, _corpus_target
    )

    ide = determine_ide()

    if ide == IDE.BROWNIE:
        artifacts = BrownieJob(target, analyze_config["build_directory"], map_to_original_source=map_to_original_source)
        artifacts.generate_payload()
    elif ide == IDE.HARDHAT:
        artifacts = HardhatJob(target, analyze_config["build_directory"], map_to_original_source=map_to_original_source)
        artifacts.generate_payload()
    elif ide == IDE.TRUFFLE:
        raise click.exceptions.UsageError(
            f"Projects using Truffle IDE is not supported right now"
        )
    else:
        raise click.exceptions.UsageError(
            f"Projects using plain solidity files is not supported right now"
        )

    faas_client = FaasClient(
        faas_url=faas_url, campaign_name_prefix=campaign_name_prefix, project_type=ide, api_key=api_key
    )
    try:
        campaign_id = faas_client.create_faas_campaign(
            campaign_data=artifacts, seed_state=seed_state, dry_run=dry_run
        )
        click.echo(
            "You can view campaign here: " + faas_url + "/campaigns/" + str(campaign_id)
        )
    except BadStatusCode as e:
        raise click.exceptions.UsageError(
            f"Campaign submission error. Detail - {e.detail}"
        )
    except Exception as e:
        LOGGER.warning(
            f"Could not submit campaign to the FaaS\n{traceback.format_exc()}"
        )
        raise click.exceptions.UsageError(
            f"Unable to submit the campaign to the faas. Are you sure the service is running on {faas_url} ?"
        )
