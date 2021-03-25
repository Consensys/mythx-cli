from pathlib import Path
import json
import os
import logging
from .exceptions import BrownieError, BuildArtifactsError, SourceError, PayloadError
LOGGER = logging.getLogger("mythx-cli")

from mythx_cli.util import sol_files_by_directory


class BrownieJob():
    def __init__(self, target: Path, build_dir: Path):
        self.target = target
        self.build_dir = build_dir
        self.source_files_paths = []
        self.contracts = []
        self.sources = {}
        self.build_files, self.build_files_by_source_file = self.find_brownie_artifacts()
        self.payload = {}

        for t in target:
            self.find_solidity_files(t)
        # removing the duplicates
        self.source_files_paths = list(set(self.source_files_paths))
        LOGGER.debug(f"Found {str(len(self.source_files_paths))} solidity files")

    def find_solidity_files(self, target_item: str):
        try:
            self.source_files_paths = sol_files_by_directory(target_item)
        except Exception as e:
           raise SourceError(f"Error finding solidity files for target {target_item}")

    def find_brownie_artifacts(self):
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

        try:
            build_files = {}
            build_files_by_source_file = {}
            # we search on Brownie's build directory
            build_dir = os.walk(self.build_dir)

            for sub_dir in build_dir:
                if len(sub_dir[2]) <= 0:
                    continue
                # sub directory with .json files
                file_prefix = sub_dir[0]
                for file in sub_dir[2]:
                    try:
                        if not file.endswith(".json"):
                            continue
                        file_name = file_prefix + "/" + file
                        with open(file_name) as json_file:
                            # load the build artifact
                            data = json.load(json_file)
                            # store it on a dictionary by file name
                            build_files[file_name] = data
                            source_path = data["sourcePath"]
                            # store it on a dictionary by source file name
                            if source_path not in build_files_by_source_file:
                                # initialize the array of contracts with a list
                                build_files_by_source_file[source_path] = []
                            build_files_by_source_file[source_path].append(data)
                    except Exception as e:
                        raise BuildArtifactsError(f"Error getting brownie artifacts for file {file}: \n {e}")
            return build_files, build_files_by_source_file
        except Exception as e:
            raise BrownieError(f"Error processing build artifacts: \n{e}")


    def generate_payload(self):
        """Generates a payload in the format consumed by the FaaS API. See {faas_url}/docs"""

        # Starts by iterating through the string list of .sol source file names listed as dependencies
        try:
            for source_file in self.source_files_paths:
                # gets the compilation artifacts for each contract in each source file
                smart_contracts = self.build_files_by_source_file.get(source_file,"")
                # each source file may have more than 1 contract, here we iterate through the contracts
                for contract in smart_contracts:
                    LOGGER.debug(f"Getting artifacts from {contract}.")
                    #We get the build items from brownie and rename them into the properties used by the FaaS
                    try:
                        faas_contract_item = {}
                        faas_contract_item["sourcePaths"] = contract["allSourcePaths"]
                        faas_contract_item["deployedSourceMap"] = contract["deployedSourceMap"]
                        faas_contract_item["deployedBytecode"] = contract["deployedBytecode"]
                        faas_contract_item["sourceMap"] = contract["sourceMap"]
                        faas_contract_item["bytecode"] = contract["bytecode"]
                        faas_contract_item["contractName"] = contract["contractName"]
                        faas_contract_item["mainSourceFile"] = contract["sourcePath"]
                    except Exception as e:
                        raise BuildArtifactsError(f"Error accessing build artifacts in {contract}: \n{e}")

                    # After getting the build items, we fetch the source code and AST
                    for file_index, source_file in contract["allSourcePaths"].items():
                        try:
                            if source_file in self.sources:
                                LOGGER.debug(f"{source_file} already included, skipping.")
                                continue
                            faas_source_item = {}
                            faas_source_item["fileIndex"] = file_index
                            if source_file not in self.build_files_by_source_file:
                                LOGGER.debug(f"{source_file} not found.")
                                continue

                            # We can select any dict on the build_files_by_source_file[source_file] array
                            # because the .source and .ast values will be the same in all.
                            target_file = self.build_files_by_source_file[source_file][0]
                            faas_source_item["source"] = target_file["source"]
                            faas_source_item["ast"] = target_file["ast"]
                            self.sources[source_file] = faas_source_item
                        except Exception as e:
                            raise SourceError(f"Error accessing source code in {source_file}: \n{e}")

                self.contracts.append(faas_contract_item)
            self.payload = {
                "contracts": self.contracts,
                "sources": self.sources
            }
        except Exception as e:
            raise PayloadError(f"Error assembling the FaaS payload from the Brownie job: \n {e}")
