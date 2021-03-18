import logging
import os
import random
import string

import requests
import click
import json
from .brownie import  BrownieJob
from .rpc import  RPCClient

from mythx_cli.analyze.scribble import ScribbleMixin

LOGGER = logging.getLogger("mythx-cli")

headers = {
    'Content-Type': 'application/json'
}

time_limit_seconds = 3000

def start_faas_campaign(payload, faas_url):
    response = (requests.request("POST", faas_url+"/api/campaigns?start_immediately=true", headers=headers, data=payload)).json()
    return response["id"]


def generate_campaign_name (prefix: str):
    letters = string.ascii_lowercase
    random_string = ''.join(random.choice(letters) for i in range(5))
    return str(prefix+"_"+random_string)

@click.command("run")
@click.argument("target", default=None, nargs=-1, required=False)
@click.option(
    "-a",
    "--address",
    type=click.STRING,
    help="Address of the main contract to analyze",
)
@click.option(
    "-m",
    "--more-addresses",
    type=click.STRING,
    help="Addresses of other contracts to analyze, separated by commas",
)

@click.pass_obj
def fuzz_run(ctx, address, more_addresses, target ):
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

    contract_address = analyze_config["deployed_contract_address"]



    rpc_url = "http://localhost:7545"
    faas_url = "http://localhost:8080"

    if 'rpc_url' in analyze_config.keys():
        rpc_url = analyze_config["rpc_url"]

    if 'faas_url' in analyze_config.keys():
        faas_url = analyze_config["faas_url"]

    rpc_client = RPCClient(rpc_url)

    number_of_cores = 2
    if 'number_of_cores' in analyze_config.keys():
        number_of_cores = analyze_config["number_of_cores"]
    contract_code_response = rpc_client.rpc_call("eth_getCode", "[\"" + contract_address + "\",\"latest\"]")

    if contract_code_response is None:
        print("Invalid address")

    if more_addresses is None:
        other_addresses=[]
    else:
        other_addresses = more_addresses.split(',')

    seed_state = rpc_client.get_seed_state(contract_address, other_addresses, number_of_cores)
    brownie = BrownieJob(target, analyze_config["build_directory"])
    brownie.generate_payload(seed_state)


    api_payload = {"parameters": {}}

    # We set the name for the campaign if there is a prefix in the config file
    # If no prefix is configured, we don't include a name in the request, and the API generates one.
    if "campaign_name_prefix" in analyze_config:
        api_payload["name"] = generate_campaign_name((analyze_config["campaign_name_prefix"]))

    api_payload["parameters"]["discovery-probability-threshold"]=seed_state["discovery-probability-threshold"]
    api_payload["parameters"]["num-cores"]=seed_state["num-cores"]
    api_payload["parameters"]["assertion-checking-mode"]=seed_state["assertion-checking-mode"]
    api_payload["corpus"] = seed_state["analysis-setup"]

    api_payload["sources"] = brownie.payload["sources"]
    api_payload["contracts"] = brownie.payload["contracts"]

    instr_meta = ScribbleMixin.get_arming_instr_meta()

    if instr_meta is not None:
        api_payload["instrumentation_metadata"] = instr_meta


    campaign_id = start_faas_campaign(json.dumps(api_payload), faas_url)
    print("You can view campaign here: "+ faas_url+"/campaigns/"+str(campaign_id))

    # print(json.dumps(api_payload))

pass
