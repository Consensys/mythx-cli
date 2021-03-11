from pathlib import Path
import json
import os
import logging
import click
LOGGER = logging.getLogger("mythx-cli")

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
        if target_item.endswith('.sol'):
            if not os.path.isfile(target_item):
                raise click.exceptions.UsageError(
                    "Could not find "+str(target_item)+". Did you pass the correct directory?"
                )
            else:
                self.source_files_paths.append(target_item)
        source_dir = os.walk(target_item)
        for sub_dir in source_dir:
            if len(sub_dir[2]) > 0:
                # sub directory with .json files
                file_prefix = sub_dir[0]
                for file in sub_dir[2]:
                    if not file.endswith(".sol"):
                        LOGGER.debug(f"Skipped for not being a solidity file: {file}")
                        continue
                    file_name = file_prefix + "/" + file
                    LOGGER.debug(f"Found solidity file: {file_name}")
                    self.source_files_paths.append(file_name)

    def find_brownie_artifacts(self):
        build_files = {}
        build_files_by_source_file = {}
        build_dir = os.walk(self.build_dir)

        for sub_dir in build_dir:
            if len(sub_dir[2]) > 0:
                # sub directory with .json files
                file_prefix = sub_dir[0]
                for file in sub_dir[2]:
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
        return build_files, build_files_by_source_file

    def generate_payload(self, execution):
        for source_file in self.source_files_paths:
            smart_contracts = self.build_files_by_source_file[source_file]
            for contract in smart_contracts:
                faas_contract_item = {}
                faas_contract_item["sourcePaths"] = contract["allSourcePaths"]
                faas_contract_item["deployedSourceMap"] = contract["deployedSourceMap"]
                faas_contract_item["deployedBytecode"] = contract["deployedBytecode"]
                faas_contract_item["sourceMap"] = contract["sourceMap"]
                faas_contract_item["bytecode"] = contract["bytecode"]
                faas_contract_item["contractName"] = contract["contractName"]
                faas_contract_item["mainSourceFile"] = contract["sourcePath"]

                for file_index, source_file in contract["allSourcePaths"].items():
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

            self.contracts.append(faas_contract_item)
        self.payload = {
            "execution": execution,
            "contracts": self.contracts,
            "sources": self.sources
        }
