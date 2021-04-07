import logging
import random
import string

import click
import requests

from mythx_cli.fuzz.ide.brownie import BrownieJob

from .exceptions import RPCCallError
from .faas import FaasClient
from .rpc import RPCClient

LOGGER = logging.getLogger("mythx-cli")

headers = {"Content-Type": "application/json"}

time_limit_seconds = 3000


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
@click.pass_obj
def fuzz_run(ctx, address, more_addresses, target):
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

    try:
        rpc_client = RPCClient(rpc_url, number_of_cores)
        contract_code_response = rpc_client.contract_exists(contract_address)
    except RPCCallError as e:
        raise click.exceptions.UsageError(f"RPC endpoint." f"\n{e}")

    if not contract_code_response:
        LOGGER.warning(f"Contract code not found")
        raise click.exceptions.ClickException(
            f"Unable to find a contract deployed at {contract_address}."
        )

    if more_addresses is None:
        other_addresses = []
    else:
        other_addresses = more_addresses.split(",")

    # We get the seed state from the provided rpc endpoint
    seed_state = rpc_client.get_seed_state(contract_address, other_addresses)
    brownie_artifacts = BrownieJob(target, analyze_config["build_directory"])
    brownie_artifacts.generate_payload()

    faas_client = FaasClient(
        faas_url=faas_url,
        campaign_name_prefix=campaign_name_prefix,
        project_type="brownie",
    )
    try:
        campaign_id = faas_client.create_faas_campaign(
            campaign_data=brownie_artifacts, seed_state=seed_state
        )
        click.echo(
            "You can view campaign here: " + faas_url + "/campaigns/" + str(campaign_id)
        )
    except Exception as e:
        LOGGER.warning(f"Could not submit campaign to the FaaS")
        raise click.exceptions.UsageError(
            f"Unable to submit the campaign to the faas. Are you sure the service is running on {faas_url} ?"
        )


pass
