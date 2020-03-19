"""This module contains functions to generate payloads for Truffle projects."""

import json
import logging
from typing import Any, Dict

from mythx_cli.payload.util import patch_truffle_bytecode, zero_srcmap_indices

LOGGER = logging.getLogger("mythx-cli")


def generate_truffle_payload(file: str) -> Dict[str, Any]:
    """Generate a MythX analysis request payload based on a truffle build
    artifact.

    This will send the following artifact entries to MythX for analysis:

    * :code:`contractName`
    * :code:`bytecode`
    * :code:`deployedBytecode`
    * :code:`sourceMap`
    * :code:`deployedSourceMap`
    * :code:`sourcePath`
    * :code:`source`
    * :code:`ast`
    * :code:`legacyAST`
    * the compiler version

    :param file: The path to the Truffle build artifact
    :return: The payload dictionary to be sent to MythX
    """

    with open(file) as af:
        artifact = json.load(af)
        LOGGER.debug(f"Loaded Truffle artifact with {len(artifact)} keys")

    return {
        "contract_name": artifact.get("contractName"),
        "bytecode": patch_truffle_bytecode(artifact.get("bytecode"))
        if artifact.get("bytecode") != "0x"
        else None,
        "deployed_bytecode": patch_truffle_bytecode(artifact.get("deployedBytecode"))
        if artifact.get("deployedBytecode") != "0x"
        else None,
        "source_map": zero_srcmap_indices(artifact.get("sourceMap"))
        if artifact.get("sourceMap")
        else None,
        "deployed_source_map": zero_srcmap_indices(artifact.get("deployedSourceMap"))
        if artifact.get("deployedSourceMap")
        else None,
        "sources": {
            artifact.get("sourcePath"): {
                "source": artifact.get("source"),
                "ast": artifact.get("ast"),
                "legacyAST": artifact.get("legacyAST"),
            }
        },
        "source_list": [artifact.get("sourcePath")],
        "main_source": artifact.get("sourcePath"),
        "solc_version": artifact["compiler"]["version"],
    }
