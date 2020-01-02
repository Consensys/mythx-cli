"""This module contains functions to generate Solidity-related payloads."""

import re

import click
import solcx
import solcx.exceptions

PRAGMA_PATTERN = r"pragma solidity [\^<>=]*(\d+\.\d+\.\d+);"


def generate_solidity_payload(file, version):
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
    :return: The payload dictionary to be sent to MythX
    """

    with open(file) as f:
        source = f.read()

    solc_version = re.findall(PRAGMA_PATTERN, source)
    if not (solc_version or version):
        # no pragma found, user needs to specify the version
        raise click.exceptions.UsageError("No pragma found - please specify a solc version with --solc-version")

    solc_version = "v" + (version or solc_version[0])

    if solc_version not in solcx.get_installed_solc_versions():
        try:
            solcx.install_solc(solc_version)
        except Exception as e:
            raise click.exceptions.UsageError("Error installing solc version {}: {}".format(solc_version, e))

    solcx.set_solc_version(solc_version, silent=True)
    try:
        result = solcx.compile_source(
            source, output_values=("abi", "ast", "bin", "bin-runtime", "srcmap", "srcmap-runtime")
        )
    except solcx.exceptions.SolcError as e:
        raise click.exceptions.UsageError("Error compiling source with solc {}: {}".format(solc_version, e))

    # sanitize weird solcx keys
    new_result = {}
    for key, value in result.items():
        new_key = key.replace("<stdin>:", "")
        new_result[new_key] = value

    result = new_result

    contract_name = list(result.keys())[0]
    creation_bytecode = result[contract_name]["bin"]
    deployed_bytecode = result[contract_name]["bin-runtime"]
    source_map = result[contract_name]["srcmap"]
    deployed_source_map = result[contract_name]["srcmap-runtime"]
    ast = result[contract_name]["ast"]

    return {
        "contract_name": contract_name,
        "main_source": file,
        "source_list": [file],
        "sources": {file: {"source": source, "ast": ast}},
        "bytecode": creation_bytecode,
        "source_map": source_map,
        "deployed_source_map": deployed_source_map,
        "deployed_bytecode": deployed_bytecode,
        "solc_version": solc_version,
    }
