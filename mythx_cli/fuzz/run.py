import logging
import os

import requests
import click
import json
from .brownie import  BrownieJob

from mythx_cli.analyze.scribble import ScribbleMixin

LOGGER = logging.getLogger("mythx-cli")

rpc_url = "http://localhost:7545"

headers = {
    'Content-Type': 'application/json'
}

time_limit_seconds = 3000

def rpc_call(method: str, params: str):
    payload = "{\"jsonrpc\":\"2.0\",\"method\":\"" + method + "\",\"params\":" + params + ",\"id\":1}"
    response = (requests.request("POST", rpc_url, headers=headers, data=payload)).json()
    return response["result"]


def get_block(latest: bool = False, block_number: int = -1):
    block_value = "latest" if latest else str(block_number)
    if not latest:
        block_value = hex(block_number)

    block = rpc_call("eth_getBlockByNumber", "[\"" + block_value + "\", true]")
    if block is None:
        return None
    else:
        return block


def get_all_blocks():
    latest_block = get_block(True)
    if not latest_block:
        return []

    blocks = []
    for i in range(0, int(latest_block["number"], 16) + 1, 1):
        blocks.append(get_block(block_number=i))
    return blocks


def get_seed_state(address: str, other_addresses: [str]):
    blocks = get_all_blocks()
    processed_transactions = []
    for block in blocks:
        for transaction in block["transactions"]:
            for key, value in dict(transaction).items():
                if value is None:
                    transaction[key] = ""
            processed_transactions.append(transaction)
    setup = dict({
        "address-under-test": address,
        "steps": processed_transactions,
        "other-addresses-under-test": other_addresses})
    return dict(
        {
            "time-limit-secs": time_limit_seconds,
            "analysis-setup": setup,
            "discovery-probability-threshold": 0.0,
            "assertion-checking-mode": 1,
            "emit-mythx-report": True
        }
    )

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

    # print FaaS dashbaord url pointing to campaign
    analyze_config = ctx.get("fuzz")
    contract_address = analyze_config["deployed_contract_address"]
    contract_code_response = rpc_call("eth_getCode", "[\"" + contract_address + "\",\"latest\"]")

    if contract_code_response is None:
        print("Invalid address")

    if more_addresses is None:
        other_addresses=[]
    else:
        other_addresses = more_addresses.split(',')

    seed_state = get_seed_state(contract_address, other_addresses)
    brownie = BrownieJob(target, analyze_config["build_directory"])
    brownie.generate_payload(seed_state)
    api_payload = brownie.payload
    instr_meta = ScribbleMixin.get_arming_instr_meta()

    if instr_meta is not None:
        api_payload["instrumentation_metadata"] = instr_meta

    print(json.dumps(api_payload))

pass
