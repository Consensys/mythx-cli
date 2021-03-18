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


class RPCClient():
    def __init__(self, rpc_url: str):
        self.rpc_url = rpc_url


    def rpc_call(self, method: str, params: str):
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


    def get_all_blocks(self):
        latest_block = self.get_block(latest=True)
        if not latest_block:
            return []

        blocks = []
        for i in range(0, int(latest_block["number"], 16) + 1, 1):
            blocks.append(self.get_block(block_number=i))
        return blocks


    def get_seed_state(self, address: str, other_addresses: [str], number_of_cores: int):
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
                "num-cores": number_of_cores
            }
        )
