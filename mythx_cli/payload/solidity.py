import solcx
import re
import click
import solcx.exceptions

PRAGMA_PATTERN = r"pragma solidity [\^<>=]*(\d+\.\d+\.\d+);"


def generate_solidity_payload(file):
    with open(file) as f:
        source = f.read()

    solc_version = re.findall(PRAGMA_PATTERN, source)
    if not solc_version:
        # no pragma found, user needs to specify the version
        raise click.exceptions.UsageError(
            "No pragma found - please specify a solc version with --solc-version"
        )
        # TODO: Pass user-defined version
    solc_version = "v" + solc_version[0]

    if solc_version not in solcx.get_installed_solc_versions():
        try:
            solcx.install_solc(solc_version)
        except Exception as e:
            raise click.exceptions.UsageError(
                "Error installing solc version {}: {}".format(solc_version, e)
            )

    solcx.set_solc_version(solc_version, silent=True)
    try:
        result = solcx.compile_source(
            source, output_values=("abi", "ast", "bin", "bin-runtime", "srcmap", "srcmap-runtime")
        )
    except solcx.exceptions.SolcError as e:
        raise click.exceptions.UsageError(
            "Error compiling source with solc {}: {}".format(solc_version, e)
        )

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
