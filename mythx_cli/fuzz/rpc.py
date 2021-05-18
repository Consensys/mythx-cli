import logging
from typing import Optional

import click
import requests
from requests import RequestException

from .exceptions import RPCCallError

LOGGER = logging.getLogger("mythx-cli")

headers = {"Content-Type": "application/json"}
time_limit_seconds = 3000
NUM_BLOCKS_UPPER_LIMIT = 9999


class RPCClient:
    def __init__(self, rpc_url: str, number_of_cores: int):
        self.rpc_url = rpc_url
        self.number_of_cores = number_of_cores

    def call(self, method: str, params: str):
        """Make an rpc call to the RPC endpoint

        :return: Result property of the RPC response
        """
        try:
            payload = (
                '{"jsonrpc":"2.0","method":"'
                + method
                + '","params":'
                + params
                + ',"id":1}'
            )
            response = (
                requests.request("POST", self.rpc_url, headers=headers, data=payload)
            ).json()
            return response["result"]
        except RequestException as e:
            raise RPCCallError(
                f"HTTP error calling RPC method {method} with parameters: {params}"
                f"\nAre you sure the RPC is running at {self.rpc_url}?"
            )

    def contract_exists(self, contract_address):
        return self.call("eth_getCode", '["' + contract_address + '","latest"]')

    def get_block(self, latest: bool = False, block_number: int = -1):
        block_value = "latest" if latest else str(block_number)
        if not latest:
            block_value = hex(block_number)

        block = self.call("eth_getBlockByNumber", '["' + block_value + '", true]')
        return block

    def get_all_blocks(self):
        """ Get all blocks from the node running at rpc_url

        Raises an exception if the number of blocks
        exceeds 10000 as it is likely a user error who passed the wrong
        RPC address.
        """
        latest_block = self.get_block(latest=True)
        if not latest_block:
            return []

        num_of_blocks = int(latest_block["number"], 16) + 1
        if num_of_blocks > NUM_BLOCKS_UPPER_LIMIT:
            raise click.exceptions.UsageError(
                "Number of blocks existing on the ethereum node running at"
                + str(self.rpc_url)
                + "can not exceed 10000. Did you pass the correct RPC url?"
            )
        blocks = []
        for i in range(0, num_of_blocks, 1):
            blocks.append(self.get_block(block_number=i))
        return blocks

    def get_seed_state(
        self, address: str, other_addresses: [str], corpus_target: Optional[str] = None
    ):
        seed_state = {
            "time-limit-secs": time_limit_seconds,
            "discovery-probability-threshold": 0.0,
            "assertion-checking-mode": 1,
            "emit-mythx-report": True,
            "num-cores": self.number_of_cores,
        }
        """Get a seed state for the target contract to be used by Harvey"""
        if corpus_target:
            return dict({**seed_state, "analysis-setup": {"target": corpus_target}})

        try:
            blocks = self.get_all_blocks()
            processed_transactions = []
            for block in blocks:
                for transaction in block["transactions"]:
                    for key, value in dict(transaction).items():
                        if value is None:
                            transaction[key] = ""
                    processed_transactions.append(transaction)
            setup = dict(
                {
                    "address-under-test": address,
                    "steps": processed_transactions,
                    "other-addresses-under-test": other_addresses,
                }
            )
            return dict({**seed_state, "analysis-setup": setup})
        except Exception as e:
            LOGGER.warning(f"Could not generate seed state for address: {address}")
            raise click.exceptions.UsageError(
                (
                    "Unable to generate the seed state for address"
                    + str(address)
                    + "Are you sure you passed the correct contract address?"
                )
            ) from e
