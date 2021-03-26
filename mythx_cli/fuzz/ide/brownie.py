from pathlib import Path
import json
import os
import logging
from mythx_cli.fuzz.exceptions import BrownieError, BuildArtifactsError, SourceError, PayloadError
LOGGER = logging.getLogger("mythx-cli")

from mythx_cli.util import sol_files_by_directory
from collections import defaultdict
from pathlib import Path
from typing import Tuple, Dict, List


class IDEArtifacts:
    @property
    def contracts(self) -> Dict:
        """ Returns sources
        sources = {
            "filename": [
                {
                    "bytecode": <>,
                    ...
                    "deployedBytecode": <>
                }
            ]
        }
        """
        pass

    @property
    def sources(self) -> Dict:
        """ Returns sources
        sources = {
            "filename": {
                "ast": <>,
                "source: ""
            }
        }
        """
        pass


class BrownieArtifacts(IDEArtifacts):
    def __init__(self, build_dir=None, targets=None):
        self._include = []
        if targets:
            include = []
            for target in targets:
                include.extend(sol_files_by_directory(target))
            self._include = include

        self._build_dir = build_dir or Path("./build/contracts")
        build_files_by_source_file = self._get_build_artifacts(self._build_dir)

        self._contracts, self._sources = self.fetch_data(build_files_by_source_file)

    @property
    def contracts(self):
        return self._contracts

    @property
    def sources(self):
        return self._sources

    def fetch_data(self, build_files_by_source_file):
        result_contracts = {}
        result_sources = {}
        for source_file, contracts in build_files_by_source_file.items():
            if source_file not in self._include:
                continue
            result_contracts[source_file] = []
            for contract in contracts:
                # We get the build items from brownie and rename them into the properties used by the FaaS
                try:
                    result_contracts[source_file] += [{
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

                for file_index, source_file_dep in contract["allSourcePaths"].items():
                    if source_file_dep in result_sources.keys():
                        continue

                    if source_file_dep not in build_files_by_source_file:
                        LOGGER.debug(f"{source_file} not found.")
                        continue

                    # We can select any dict on the build_files_by_source_file[source_file] array
                    # because the .source and .ast values will be the same in all.
                    target_file = build_files_by_source_file[source_file_dep][0]
                    result_sources[source_file_dep] = {
                        "fileIndex": file_index,
                        "source": target_file["source"],
                        "ast": target_file["ast"],
                    }
        return result_contracts, result_sources

    @staticmethod
    def _get_build_artifacts(build_dir) -> Dict:
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
            source_path = data["sourcePath"]

            if source_path not in build_files_by_source_file:
                # initialize the array of contracts with a list
                build_files_by_source_file[source_path] = []

            build_files_by_source_file[source_path].append(data)

        return build_files_by_source_file


class JobBuilder:
    def __init__(self, artifacts: IDEArtifacts):
        self._artifacts = artifacts

    def payload(self):
        sources = self._artifacts.sources
        contracts = [c for contracts_for_file in self._artifacts.contracts.values() for c in contracts_for_file]
        return {
            "contracts": contracts,
            "sources": sources
        }


class BrownieJob:
    def __init__(self, target: List[str], build_dir: Path):
        artifacts = BrownieArtifacts(build_dir, targets=target)
        self._jb = JobBuilder(artifacts)
        self.payload = None

    def generate_payload(self):
        self.payload = self._jb.payload()
