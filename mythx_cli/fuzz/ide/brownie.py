from pathlib import Path
import json
import os
import logging
from mythx_cli.fuzz.exceptions import BrownieError, BuildArtifactsError, SourceError, PayloadError
LOGGER = logging.getLogger("mythx-cli")

from mythx_cli.util import sol_files_by_directory
from collections import defaultdict
from pathlib import Path
from typing import Tuple, Dict

class IDEArtifacts:
    @property
    def contracts(self):
        pass

    @property
    def sources(self):
        pass

    def get_source_data(self, source_path) -> Dict:
        pass

    def get_contract_data(self, source_path, contract_name):
        pass


class BrownieArtifacts:
    def __init__(self, build_dir=None):
        self._build_dir = build_dir or Path("./build/contracts")
        build_files, build_files_by_source_file = self._get_build_artifacts(self._build_dir)

        self._contracts = self.populate_contracts(build_files, build_files_by_source_file)
        self._sources = self.populate_sources(self._contracts, build_files_by_source_file)

    @property
    def contracts(self):
        return self._contracts

    @property
    def sources(self):
        return self._contracts

    def get_source_data(self, source_path) -> Dict:
        return self._contracts.get(source_path, None)

    def get_contract_data(self, source_path, contract_name):
        return self._contracts.get(source_path, {}).get(contract_name, None)

    @staticmethod
    def populate_contracts(build_files, build_files_by_source_file):
        contracts = {}
        for source_file, contracts in build_files_by_source_file.values():
            contracts[source_file] = {}
            for contract in contracts:
                LOGGER.debug(f"Getting artifacts from {contract}.")

                # We get the build items from brownie and rename them into the properties used by the FaaS
                try:
                    contracts[source_file][contract] ={
                        "sourcePaths": contract["allSourcePaths"],
                        "deployedSourceMap": contract["deployedSourceMap"],
                        "deployedBytecode": contract["deployedBytecode"],
                        "sourceMap": contract["sourceMap"],
                        "bytecode": contract["bytecode"],
                        "contractName": contract["contractName"],
                        "mainSourceFile": contract["sourcePath"],
                    }
                except KeyError as e:
                    raise BuildArtifactsError(
                        f"Build artifact did not contain expected key. Contract: {contract}: \n{e}"
                    )
        return contracts

    @staticmethod
    def populate_sources(contracts, build_files_by_source_file):
        sources = {}
        for source_file, contracts in contracts.items():
            for contract_name, contract in contracts.items():
                for file_index, source_file in contract["allSourcePaths"].items():
                    if source_file in sources:
                        continue

                    if source_file not in build_files_by_source_file:
                        LOGGER.debug(f"{source_file} not found.")
                        continue

                    # We can select any dict on the build_files_by_source_file[source_file] array
                    # because the .source and .ast values will be the same in all.
                    target_file = build_files_by_source_file[source_file][0]
                    sources[source_file] = {
                        "fileIndex": file_index,
                        "source": target_file["source"],
                        "ast": target_file["ast"],
                    }
        return sources

    @staticmethod
    def _get_build_artifacts(build_dir) -> Tuple[Dict, Dict]:
        """Build indexes of Brownie build artifacts.

        This function starts by loading the contents from the Brownie build artifacts json, found in the /build
        folder, which contain the following data:

        * :code: `allSourcePaths`
        * :code: `deployedSourceMap`
        * :code: `deployedBytecode`
        * :code: `sourceMap`
        * :code: `bytecode`
        * :code: `contractName`
        * :code: `sourcePath`

        It then stores that data in two separate dictionaires, build_files and build_files_by_source_file. The first
        is indexed by the compilation artifact file name (the json found in /build/*) and the second is indexed by the
        source file (.sol) found in the .sourcePath property of the json.
        """
        build_files = {}
        build_files_by_source_file = {}

        build_dir = Path(build_dir)

        if not build_dir.is_dir():
            raise BuildArtifactsError("Build directory doesn't exist")

        for child in build_dir.iterdir():
            if not child.is_file():
                continue
            if not child.name.endswith(".json"):
                continue

            data = json.loads(child.read_text('utf-8'))
            build_files[child.name] = data
            source_path = data["sourcePath"]

            if source_path not in build_files_by_source_file:
                # initialize the array of contracts with a list
                build_files_by_source_file[source_path] = []

            build_files_by_source_file[source_path].append(data)

        return build_files, build_files_by_source_file


class BrownieJobBuilder:
    def __init__(self):
        pass

    def generate_payload(self, target: Path, build_directory: Path):
        sources, contracts = {}, {}

        build_files, build_files_by_source_file = BrownieArtifacts.get_build_artifacts(build_directory)
        for source_file in sol_files_by_directory(target):
            for contract in build_files_by_source_file.get(source_file, None):
                if not contract:
                    continue
                LOGGER.debug(f"Getting artifacts from {contract}.")

                # We get the build items from brownie and rename them into the properties used by the FaaS
                try:
                    contracts += [{
                        "sourcePaths": contract["allSourcePaths"],
                        "deployedSourceMap": contract["deployedSourceMap"],
                        "deployedBytecode": contract["deployedBytecode"],
                        "sourceMap": contract["sourceMap"],
                        "bytecode": contract["bytecode"],
                        "contractName": contract["contractName"],
                        "mainSourceFile": contract["sourcePath"],
                    }]
                except KeyError as e:
                    raise BuildArtifactsError(
                        f"Build artifact did not contain expected key. Contract: {contract}: \n{e}"
                    )

                # After getting the build items, we fetch the source code and AST
                for file_index, source_file in contract["allSourcePaths"].items():
                    if source_file in sources:
                        continue

                    if source_file not in build_files_by_source_file:
                        LOGGER.debug(f"{source_file} not found.")
                        continue

                    # We can select any dict on the build_files_by_source_file[source_file] array
                    # because the .source and .ast values will be the same in all.
                    target_file = build_files_by_source_file[source_file][0]
                    sources[source_file] = {
                        "fileIndex": file_index,
                        "source": target_file["source"],
                        "ast": target_file["ast"],
                    }
        return {
            "contracts": contracts,
            "sources": sources
        }

