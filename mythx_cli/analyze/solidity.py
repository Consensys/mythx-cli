"""This module contains functions to generate Solidity-related payloads."""

import logging
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import click
import solcx
import solcx.exceptions

LOGGER = logging.getLogger("mythx-cli")
PRAGMA_PATTERN = r"pragma solidity [\^<>=]*(\d+\.\d+\.\d+);"
RGLOB_BLACKLIST = ["node_modules"]


def patch_solc_bytecode(code: str) -> str:
    """Patch solc bytecode placeholders.

    This function patches placeholders in solc output. These placeholders are meant
    to be replaced with deployed library/dependency addresses on deployment, but do not form
    valid EVM bytecode. To produce a valid payload, placeholders are replaced with the zero-address.

    :param code: The bytecode to patch
    :return: The patched bytecode with the zero-address filled in
    """
    return re.sub(re.compile(r"__\$.{34}\$__"), "0" * 40, code)


def walk_solidity_files(
    ctx,
    solc_version: str,
    base_path: Optional[str] = None,
    remappings: Tuple[str] = None,
) -> List[Dict]:
    """Aggregate all Solidity files in the given base path.

    Given a base path, this function will recursively walk through the filesystem
    and aggregate all Solidity files it comes across. The resulting job list will
    contain all the Solidity payloads (optionally compiled), ready for submission.

    :param ctx: :param ctx: Click context holding group-level parameters
    :param solc_version: The solc version to use for Solidity compilation
    :param base_path: The base path to walk through from
    :param remappings: Import remappings to pass to solcx
    :return:
    """

    jobs = []
    remappings = remappings or []
    LOGGER.debug(f"Received {len(remappings)} import remappings")
    walk_path = Path(base_path) if base_path else Path.cwd()
    LOGGER.debug(f"Walking for sol files under {walk_path}")

    files = [str(x) for x in walk_path.rglob("*.sol")]
    if not files:
        LOGGER.debug(f"No Solidity files found in pattern {walk_path}")
        return jobs
    files = [af for af in files if all((b not in af for b in RGLOB_BLACKLIST))]

    consent = ctx["yes"] or click.confirm(
        f"Found {len(files)} Solidity file(s) before filtering. Continue?"
    )
    if not consent:
        LOGGER.debug("User consent not given - exiting")
        sys.exit(0)

    LOGGER.debug(f"Found Solidity files to submit: {', '.join(files)}")
    for file in files:
        LOGGER.debug(f"Generating Solidity payload for {file}")
        jobs.append(
            generate_solidity_payload(file, solc_version, remappings=remappings)
        )
    return jobs


def generate_solidity_payload(
    file: str,
    version: Optional[str],
    contract: str = None,
    remappings: Tuple[str] = None,
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
    :param contract: The contract name(s) to submit
    :param remappings: Import remappings to pass to solcx
    :return: The payload dictionary to be sent to MythX
    """

    with open(file) as f:
        source = f.read()

    solc_version = re.findall(PRAGMA_PATTERN, source)
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
        result = solcx.compile_standard(
            input_data={
                "language": "Solidity",
                "sources": {file: {"urls": [file]}},
                "settings": {
                    "remappings": [r.format(pwd=cwd) for r in remappings]
                    or [
                        f"openzeppelin-solidity/={cwd}/node_modules/openzeppelin-solidity/",
                        f"openzeppelin-zos/={cwd}/node_modules/openzeppelin-zos/",
                        f"zos-lib/={cwd}/node_modules/zos-lib/",
                    ],
                    "outputSelection": {
                        "*": {
                            "*": [
                                "evm.bytecode.object",
                                "evm.bytecode.sourceMap",
                                "evm.deployedBytecode.object",
                                "evm.deployedBytecode.sourceMap",
                            ],
                            "": ["ast"],
                        }
                    },
                    "optimizer": {"enabled": True, "runs": 200},
                },
            },
            allow_paths=cwd,
        )
    except solcx.exceptions.SolcError as e:
        raise click.exceptions.UsageError(
            f"Error compiling source with solc {solc_version}: {e}"
        )

    compiled_sources = result.get("sources", {})

    payload = {
        "sources": {},
        "solc_version": solc_version,
        "main_source": file,
        "source_list": [None] * len(compiled_sources),
    }

    for file_path, file_data in compiled_sources.items():
        # fill source list entry
        payload["source_list"][file_data.get("id")] = file_path

        payload_dict = payload["sources"][file_path] = {}

        # add AST for file if it's present
        ast = file_data.get("ast")
        if ast:
            payload_dict["ast"] = ast

        # add source from file path
        with open(file_path, newline="") as source_f:
            payload_dict["source"] = source_f.read()

    if contract:
        try:
            # if contract specified, set its bytecode and source mapping
            payload["contract_name"] = contract
            payload["bytecode"] = patch_solc_bytecode(
                result["contracts"][file][contract]["evm"]["bytecode"]["object"]
            )
            payload["source_map"] = result["contracts"][file][contract]["evm"][
                "bytecode"
            ]["sourceMap"]
            payload["deployed_bytecode"] = patch_solc_bytecode(
                result["contracts"][file][contract]["evm"]["deployedBytecode"]["object"]
            )
            payload["deployed_source_map"] = result["contracts"][file][contract]["evm"][
                "deployedBytecode"
            ]["sourceMap"]
            return payload
        except KeyError:
            LOGGER.warning(
                f"Could not find contract {contract} in compilation artifacts. The CLI will find the "
                f"largest bytecode artifact in the compilation output and submit it instead."
            )

    # extract the largest bytecode from the compilation result and add it
    bytecode_max = 0
    for file_path, file_element in result.get("contracts", {}).items():
        for contract, contract_data in file_element.items():
            contract_bytecode = contract_data["evm"]["bytecode"]["object"]
            contract_source_map = contract_data["evm"]["bytecode"]["sourceMap"]
            contract_deployed_bytecode = contract_data["evm"]["deployedBytecode"][
                "object"
            ]
            contract_deployed_source_map = contract_data["evm"]["deployedBytecode"][
                "sourceMap"
            ]
            bytecode_length = len(contract_bytecode)
            if bytecode_length > bytecode_max:
                bytecode_max = bytecode_length
                payload["contract_name"] = contract
                payload["bytecode"] = patch_solc_bytecode(contract_bytecode)
                payload["source_map"] = contract_source_map
                payload["deployed_bytecode"] = patch_solc_bytecode(
                    contract_deployed_bytecode
                )
                payload["deployed_source_map"] = contract_deployed_source_map

    return payload
