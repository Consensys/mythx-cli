from pathlib import Path
import json
import os
import logging
import click
import requests

LOGGER = logging.getLogger("mythx-cli")

headers = {
    'Content-Type': 'application/json'
}
time_limit_seconds = 3000
NUM_BLOCKS_UPPER_LIMIT = 9999

# TODO: separate into an RPC class and a Harvey class
class RPCClient():
    def __init__(self, rpc_url: str, number_of_cores: int):
        self.rpc_url = rpc_url
        self.number_of_cores = number_of_cores

    """Makes an rpc call to the RPC endpoint passed to the construcotr
    and returns the `result` property of the rpc response.
    """
    # TODO: rename to call
    def rpc_call(self, method: str, params: str):
        # TODO: add try catch, use the base exceptions if available
        payload = "{\"jsonrpc\":\"2.0\",\"method\":\"" + method + "\",\"params\":" + params + ",\"id\":1}"
        response = (requests.request("POST", self.rpc_url, headers=headers, data=payload)).json()
        return response["result"]

    def get_block(self, latest: bool = False, block_number: int = -1):
        block_value = "latest" if latest else str(block_number)
        if not latest:
            block_value = hex(block_number)

        block = self.rpc_call("eth_getBlockByNumber", "[\"" + block_value + "\", true]")
        if block is None:
            return None
        else:
            return block

    """Returns all the blocks that exist on the target
    ethereum node. Raises an exception if the number of blocks
    exceeds 10000 as it is likely a user error who passed the wrong
    RPC address.
    """

    def get_all_blocks(self):
        latest_block = self.get_block(latest=True)
        if not latest_block:
            return []

        num_of_blocks = int(latest_block["number"], 16) + 1
        if num_of_blocks > NUM_BLOCKS_UPPER_LIMIT:
            raise click.exceptions.UsageError(
                "Number of blocks existing on the ethereum node running at"
                + str(self.rpc_url) + "can not exceed 10000. Did you pass the correct RPC url?"
            )
        blocks = []
        for i in range(0, num_of_blocks, 1):
            blocks.append(self.get_block(block_number=i))
        return blocks

    """Returns a seed state for the target contract in a format that can be used by
    the FaaS API and Harvey.
    """
    def get_seed_state(self, address: str, other_addresses: [str]):
        try:
            blocks = self.get_all_blocks()
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
                    "emit-mythx-report": True,
                    "num-cores": self.number_of_cores
                }
            )
        except:
            LOGGER.warning(f"Could generate seed state for address: {address}")
            click.echo(
                (
                    "Unable to generate the seed state for address"
                    + str(address)
                    + "Are you sure you passed the correct contract address?"
                )
            )
