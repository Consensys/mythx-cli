"""This module contains functions to generate Solidity-related payloads."""

import logging
import re
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

    def payload_from_sources(
        self, solc_result: Dict, scribble_file: str, solc_version: str
    ) -> Dict:
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

    def solc_version_from_source(self, source: str, default_version: str):
        solc_version = re.findall(PRAGMA_PATTERN, source)
        LOGGER.debug(f"solc version matches in {self.target}: {solc_version}")

        if not (solc_version or default_version):
            # no pragma found, user needs to specify the version
            raise click.exceptions.UsageError(
                "No pragma found - please specify a solc version with --solc-version"
            )

        return f"v{default_version or solc_version[0]}"

    @staticmethod
    def setup_solcx(solc_version: str):
        if solc_version not in solcx.get_installed_solc_versions():
            try:
                LOGGER.debug(f"Installing solc {solc_version}")
                solcx.install_solc(solc_version)
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

    def set_payload_bytecode_context(self, payload: Dict, solc_result: Dict):
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

    def solcx_compile(
        self,
        path: str,
        remappings: Tuple[str],
        enable_scribble: bool,
        scribble_file: str = None,
        solc_path: str = None,
    ) -> Dict:
        return solcx.compile_standard(
            solc_binary=solc_path,
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
        solc_path: Optional[str] = None,
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
        :param solc_path: The path to a custom solc executable
        :param contract: The contract name(s) to submit
        :param remappings: Import remappings to pass to solcx
        :param enable_scribble: Enable instrumentation with scribble
        :param scribble_path: Optional path to the scribble executable
        """

        with open(self.target) as f:
            source = f.read()

        solc_version = None
        if solc_path is None:
            solc_version = self.solc_version_from_source(
                source=source, default_version=version
            )
            self.setup_solcx(solc_version)

        if enable_scribble:
            # use scribble for compilation
            result = self.instrument_solc_file(
                target=self.target, scribble_path=scribble_path, remappings=remappings
            )
        else:
            try:
                cwd = str(Path.cwd().absolute())
                LOGGER.debug(f"Compiling {self.target} under allowed path {cwd}")
                result = self.solcx_compile(
                    path=cwd,
                    remappings=remappings,
                    enable_scribble=enable_scribble,
                    solc_path=solc_path,
                )
            except solcx.exceptions.SolcError as e:
                raise click.exceptions.UsageError(
                    f"Error compiling source with solc {solc_version}: {e}"
                )

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
                return
            except KeyError:
                LOGGER.warning(
                    f"Could not find contract {contract} in compilation artifacts. The CLI will "
                    f"find the largest bytecode artifact in the compilation output and submit it "
                    f"instead."
                )

        self.set_payload_bytecode_context(payload, result)
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
        solc_path: Optional[str] = None,
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
        :param solc_path: The path to a custom solc executable
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
                version=solc_version,
                solc_path=solc_path,
                remappings=remappings,
                enable_scribble=enable_scribble,
                scribble_path=scribble_path,
            )
            LOGGER.debug(f"Generating Solidity payload for {file}")
            jobs.extend(job.payloads)
        return jobs
