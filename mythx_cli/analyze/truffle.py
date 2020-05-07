"""This module contains functions to generate payloads for Truffle projects."""

import json
import logging
import re
from copy import copy
from glob import glob
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

LOGGER = logging.getLogger("mythx-cli")


def set_srcmap_indices(src_map: str, index: int = 0) -> str:
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
            fields[2] = str(index)
            new_entries[i] = ":".join(fields)
    return ";".join(new_entries)


def find_truffle_artifacts(project_dir: Union[str, Path]) -> Optional[List[str]]:
    """Look for a Truffle build folder and return all relevant JSON artifacts.

    This function will skip the Migrations.json file and return all other files
    under :code:`<project-dir>/build/contracts/`. If no files were found,
    :code:`None` is returned.

    :param project_dir: The base directory of the Truffle project
    :return: Files under :code:`<project-dir>/build/contracts/` or :code:`None`
    """

    output_pattern = Path(project_dir) / "build" / "contracts" / "*.json"
    artifact_files = list(glob(str(output_pattern.absolute())))
    if not artifact_files:
        LOGGER.debug(f"No truffle artifacts found in pattern {output_pattern}")
        return None

    LOGGER.debug("Returning results without Migrations.json")
    return [f for f in artifact_files if not f.endswith("Migrations.json")]


def patch_truffle_bytecode(code: str) -> str:
    """Patch Truffle bytecode placeholders.

    This function patches placeholders in Truffle artifact files. These placeholders are meant
    to be replaced with deployed library/dependency addresses on deployment, but do not form
    valid EVM bytecode. To produce a valid payload, placeholders are replaced with the zero-address.

    :param code: The bytecode to patch
    :return: The patched bytecode with the zero-address filled in
    """
    return re.sub(re.compile(r"__\w{38}"), "0" * 40, code)


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
        "source_map": set_srcmap_indices(artifact.get("sourceMap"))
        if artifact.get("sourceMap")
        else None,
        "deployed_source_map": set_srcmap_indices(artifact.get("deployedSourceMap"))
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
