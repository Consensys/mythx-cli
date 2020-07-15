"""This module contains functions to generate Solidity-related payloads."""

import json
import logging
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import click
import solcx
import solcx.exceptions

from .scribble import ScribbleMixin

LOGGER = logging.getLogger("mythx-cli")
PRAGMA_PATTERN = r"pragma solidity [\^<>=]*(\d+\.\d+\.\d+);"
RGLOB_BLACKLIST = ["node_modules"]


class SolidityJob(ScribbleMixin):
    def __init__(self, target: Path):
        super().__init__()
        self.target = str(target)
        self.payloads = []

    def payload_from_sources(self, solc_result, scribble_file, solc_version):
        compiled_sources = solc_result.get("sources", {})
        payload = {
            "sources": {},
            "solc_version": solc_version,
            "main_source": scribble_file or self.target,
            "source_list": [None] * len([x for x in compiled_sources if x != "source"]),
        }

        for file_path, file_data in compiled_sources.items():
            if type(file_data) is str:
                continue
            # fill source list entry
            payload["source_list"][file_data.get("id")] = file_path
            payload_dict = payload["sources"][file_path] = {}

            # add AST for file if it's present
            ast = file_data.get("ast")
            if ast:
                payload_dict["ast"] = ast

            if scribble_file is not None:
                # add source from scribble return value
                payload_dict["source"] = compiled_sources["source"]
            else:
                # add source from file path
                with open(file_path, newline="") as source_f:
                    payload_dict["source"] = source_f.read()

        return payload

    def solc_version_from_source(self, source, default_version):
        solc_version = re.findall(PRAGMA_PATTERN, source)
        LOGGER.debug(f"solc version matches in {self.target}: {solc_version}")

        if not (solc_version or default_version):
            # no pragma found, user needs to specify the version
            raise click.exceptions.UsageError(
                "No pragma found - please specify a solc version with --solc-version"
            )

        return f"v{default_version or solc_version[0]}"

    @staticmethod
    def setup_solcx(solc_version):
        if solc_version not in solcx.get_installed_solc_versions():
            try:
                LOGGER.debug(f"Installing solc {solc_version}")
                solcx.install_solc(solc_version, allow_osx=True)
            except Exception as e:
                raise click.exceptions.UsageError(
                    f"Error installing solc version {solc_version}: {e}"
                )
        solcx.set_solc_version(solc_version, silent=True)

    def set_payload_contract_context(
        self, payload, contract, solc_result, scribble_file
    ):
        # if contract specified, set its bytecode and source mapping
        payload["contract_name"] = contract
        payload["bytecode"] = self.patch_solc_bytecode(
            solc_result["contracts"][scribble_file or self.target][contract]["evm"][
                "bytecode"
            ]["object"]
        )
        payload["source_map"] = solc_result["contracts"][scribble_file or self.target][
            contract
        ]["evm"]["bytecode"]["sourceMap"]
        payload["deployed_bytecode"] = self.patch_solc_bytecode(
            solc_result["contracts"][scribble_file or self.target][contract]["evm"][
                "deployedBytecode"
            ]["object"]
        )
        payload["deployed_source_map"] = solc_result["contracts"][
            scribble_file or self.target
        ][contract]["evm"]["deployedBytecode"]["sourceMap"]

        return payload

    def set_payload_bytecode_context(self, payload, solc_result):
        # extract the largest bytecode from the compilation result and add it
        bytecode_max = 0
        for file_path, file_element in solc_result.get("contracts", {}).items():
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
                    payload["bytecode"] = self.patch_solc_bytecode(contract_bytecode)
                    payload["source_map"] = contract_source_map
                    payload["deployed_bytecode"] = self.patch_solc_bytecode(
                        contract_deployed_bytecode
                    )
                    payload["deployed_source_map"] = contract_deployed_source_map

    def solcx_compile(self, path, remappings, enable_scribble, scribble_file=None):
        return solcx.compile_standard(
            input_data={
                "language": "Solidity",
                "sources": {
                    scribble_file
                    or self.target: {"urls": [scribble_file or self.target]}
                },
                "settings": {
                    "remappings": [r.format(pwd=path) for r in remappings]
                    or [
                        f"openzeppelin-solidity/={path}/node_modules/openzeppelin-solidity/",
                        f"openzeppelin-zos/={path}/node_modules/openzeppelin-zos/",
                        f"zos-lib/={path}/node_modules/zos-lib/",
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
            # if scribble enabled, allow access to temporary file
            allow_paths=path if not enable_scribble else scribble_file,
        )

    def generate_payloads(
        self,
        version: Optional[str],
        contract: str = None,
        remappings: Tuple[str] = None,
        enable_scribble: bool = False,
        scribble_path: str = "scribble",
    ):
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

        :param version: The solc version to use for compilation
        :param contract: The contract name(s) to submit
        :param remappings: Import remappings to pass to solcx
        :param enable_scribble: Enable instrumentation with scribble
        :param scribble_path: Optional path to the scribble executable
        """

        with open(self.target) as f:
            source = f.read()

        solc_version = self.solc_version_from_source(
            source=source, default_version=version
        )

        if enable_scribble:
            # use scribble for compilation
            result = self.instrument_solc_file(self.target, scribble_path, remappings)
        else:
            # use solc for compilation
            self.setup_solcx(solc_version)
            try:
                cwd = str(Path.cwd().absolute())
                LOGGER.debug(f"Compiling {self.target} under allowed path {cwd}")
                result = self.solcx_compile(cwd, remappings, enable_scribble)
            except solcx.exceptions.SolcError as e:
                raise click.exceptions.UsageError(
                    f"Error compiling source with solc {solc_version}: {e}"
                )

        # instrument with scribble if requested
        # scribble_file = None
        # if enable_scribble:
        #     process = subprocess.run(
        #         [scribble_path, self.target],
        #         stdout=subprocess.PIPE,
        #         stderr=subprocess.PIPE,
        #     )
        #     if process.returncode != 0:
        #         click.echo(
        #             f"Scribble has encountered an error (code: {process.returncode})"
        #         )
        #         click.echo("=====STDERR=====")
        #         click.echo(process.stderr.decode())
        #         click.echo("=====STDOUT=====")
        #         process.stdout.decode()
        #         sys.exit(process.returncode)
        #
        #     # don't delete temp file on close but manually unlink
        #     # after payload has been generated
        #     scribble_output_f = tempfile.NamedTemporaryFile(
        #         mode="w+", delete=False, suffix=".sol"
        #     )
        #     scribble_stdout = process.stdout.decode()
        #     scribble_output_f.write(scribble_stdout)
        #     scribble_file = scribble_output_f.name
        #     scribble_output_f.close()

        payload = self.payload_from_sources(
            solc_result=result,
            solc_version=solc_version,
            scribble_file="flattened.sol" if enable_scribble else None,
        )

        if contract:
            LOGGER.debug("Contract specified - targeted payload selection")
            try:
                self.payloads.append(
                    self.set_payload_contract_context(
                        payload=payload,
                        contract=contract,
                        solc_result=result,
                        scribble_file=None,
                    )
                )
            except KeyError:
                LOGGER.warning(
                    f"Could not find contract {contract} in compilation artifacts. The CLI will find the "
                    f"largest bytecode artifact in the compilation output and submit it instead."
                )

        self.set_payload_bytecode_context(payload, result)

        # if enable_scribble:
        #     # replace scribble tempfile name with prefixed one
        #     scribble_payload = payload["sources"].pop(scribble_file)
        #     payload["sources"]["scribble-" + str(self.target)] = scribble_payload
        #     payload["source_list"] = [
        #         "scribble-" + str(self.target) if item == scribble_file else item
        #         for item in payload["source_list"]
        #     ]
        #     payload["main_source"] = "scribble-" + str(self.target)
        #
        #     # delete scribble temp file
        #     os.unlink(scribble_file)

        # print(json.dumps(payload))
        # sys.exit()
        self.payloads.append(payload)

    @staticmethod
    def patch_solc_bytecode(code: str) -> str:
        """Patch solc bytecode placeholders.

        This function patches placeholders in solc output. These placeholders are meant
        to be replaced with deployed library/dependency addresses on deployment, but do not form
        valid EVM bytecode. To produce a valid payload, placeholders are replaced with the zero-address.

        :param code: The bytecode to patch
        :return: The patched bytecode with the zero-address filled in
        """
        return re.sub(re.compile(r"__\$.{34}\$__"), "0" * 40, code)

    @classmethod
    def walk_solidity_files(
        cls,
        solc_version: str,
        base_path: Optional[str] = None,
        remappings: Tuple[str] = None,
        enable_scribble: bool = False,
        scribble_path: str = "scribble",
    ) -> List[Dict]:
        """Aggregate all Solidity files in the given base path.

        Given a base path, this function will recursively walk through the filesystem
        and aggregate all Solidity files it comes across. The resulting job list will
        contain all the Solidity payloads (optionally compiled), ready for submission.

        :param solc_version: The solc version to use for Solidity compilation
        :param base_path: The base path to walk through from
        :param remappings: Import remappings to pass to solcx
        :param enable_scribble: Enable instrumentation with scribble
        :param scribble_path: Optional path to the scribble executable
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

        LOGGER.debug(f"Found Solidity files to submit: {', '.join(files)}")
        for file in files:
            job = cls(Path(file))
            job.generate_payloads(
                solc_version,
                remappings=remappings,
                enable_scribble=enable_scribble,
                scribble_path=scribble_path,
            )
            LOGGER.debug(f"Generating Solidity payload for {file}")
            jobs.extend(job.payloads)
        return jobs
