"""This module contains functions to generate payloads for Truffle projects."""

import json
import re
from copy import copy


def patch_bytecode(code):
    return re.sub(re.compile(r"__\w{38}"), "0" * 40, code)


def zero_srcmap_indices(src_map: str) -> str:
    """Zero the source map file index entries.

    :param src_map: The source map string to process
    :return: The processed source map string
    """
    entries = src_map.split(";")
    new_entries = copy(entries)
    for i, entry in enumerate(entries):
        fields = entry.split(":")
        if len(fields) > 2 and fields[2] not in ("-1", ""):
            # file index is in entry, needs fixing
            fields[2] = "0"
            new_entries[i] = ":".join(fields)
    return ";".join(new_entries)


def generate_truffle_payload(file):
    """Generate a MythX analysis request payload based on a truffle build artifact.

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

    return {
        "contract_name": artifact.get("contractName"),
        "bytecode": patch_bytecode(artifact.get("bytecode")) if artifact.get("bytecode") != "0x" else None,
        "deployed_bytecode": patch_bytecode(artifact.get("deployedBytecode"))
        if artifact.get("deployedBytecode") != "0x"
        else None,
        "source_map": zero_srcmap_indices(artifact.get("sourceMap")) if artifact.get("sourceMap") else None,
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
