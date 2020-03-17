"""This module contains functions to generate Solidity-related payloads."""

import logging
import re
from pathlib import Path
from typing import Dict, List, Optional

import click
import solcx
import solcx.exceptions

from mythx_cli.payload.util import patch_solc_bytecode, zero_srcmap_indices

LOGGER = logging.getLogger("mythx-cli")
PRAGMA_PATTERN = r"pragma solidity [\^<>=]*(\d+\.\d+\.\d+);"


def generate_solidity_payload(
    file: str, version: Optional[str], contracts: List[str] = None
) -> Dict:
    """Generate a MythX analysis request from a given Solidity file.

    This function will open the file, try to detect the used solc version from
    the pragma definition, and automatically compile it. If the given solc
    version is not installed on the client's system, it will be automatically
    downloaded.

    From the solc output, the following data is sent to the MythX API for
    analysis:

    * :code:`abi`
    * :code:`ast`
    * :code:`bin`
    * :code:`bin-runtime`
    * :code:`srcmap`
    * :code:`srcmap-runtime`

    :param file: The path pointing towards the Solidity file
    :param version: The solc version to use for compilation
    :param contracts: The contract name(s) to submit
    :return: The payload dictionary to be sent to MythX
    """

    with open(file) as f:
        solc_version = re.findall(PRAGMA_PATTERN, f.read())
    LOGGER.debug(f"solc version matches in {file}: {solc_version}")

    if not (solc_version or version):
        # no pragma found, user needs to specify the version
        raise click.exceptions.UsageError(
            "No pragma found - please specify a solc version with --solc-version"
        )

    solc_version = f"v{version or solc_version[0]}"

    if solc_version not in solcx.get_installed_solc_versions():
        try:
            LOGGER.debug(f"Installing solc {solc_version}")
            solcx.install_solc(solc_version)
        except Exception as e:
            raise click.exceptions.UsageError(
                f"Error installing solc version {solc_version}: {e}"
            )

    solcx.set_solc_version(solc_version, silent=True)
    try:
        cwd = str(Path.cwd().absolute())
        LOGGER.debug(f"Compiling {file} under allowed path {cwd}")
        result = solcx.compile_files(
            [file],
            output_values=(
                "abi",
                "ast",
                "bin",
                "bin-runtime",
                "srcmap",
                "srcmap-runtime",
            ),
            import_remappings=[
                f"openzeppelin-solidity/={cwd}/node_modules/openzeppelin-solidity/"
            ],
            allow_paths=cwd,
        )
    except solcx.exceptions.SolcError as e:
        raise click.exceptions.UsageError(
            f"Error compiling source with solc {solc_version}: {e}"
        )

    # sanitize solcx keys
    new_result = {}
    for key, value in result.items():
        new_key = key.split(":")[1]
        new_result[new_key] = value
    result = new_result

    for contract_name, contract_data in result.items():
        if contracts and contract_name not in contracts:
            continue

        creation_bytecode = contract_data["bin"]
        deployed_bytecode = contract_data["bin-runtime"]
        source_map = contract_data["srcmap"]
        deployed_source_map = contract_data["srcmap-runtime"]
        ast = contract_data["ast"]
        source_path = str(Path(ast.get("attributes", {}).get("absolutePath")))
        with open(source_path) as source_f:
            source = source_f.read()

        yield {
            "contract_name": contract_name,
            "main_source": source_path,
            "source_list": [source_path],
            "sources": {source_path: {"source": source, "ast": ast}},
            "bytecode": patch_solc_bytecode(creation_bytecode),
            "source_map": zero_srcmap_indices(source_map),
            "deployed_source_map": zero_srcmap_indices(deployed_source_map),
            "deployed_bytecode": patch_solc_bytecode(deployed_bytecode),
            "solc_version": solc_version,
        }
