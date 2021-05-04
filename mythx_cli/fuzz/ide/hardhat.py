import json
from os.path import commonpath, relpath
from pathlib import Path
from typing import List

from mythx_cli.fuzz.exceptions import BuildArtifactsError
from mythx_cli.fuzz.ide.generic import IDEArtifacts, JobBuilder

from ...util import sol_files_by_directory


class HardhatArtifacts(IDEArtifacts):
    def __init__(self, build_dir=None, targets=None):
        self._include = []
        if targets:
            include = []
            for target in targets:
                include.extend(sol_files_by_directory(target))
            self._include = include

        self._build_dir = Path(build_dir).absolute() or Path("./artifacts").absolute()
        self._contracts, self._sources = self.fetch_data()

    @property
    def contracts(self):
        return self._contracts

    @property
    def sources(self):
        return self._sources

    def fetch_data(self):
        result_contracts = {}
        result_sources = {}

        for file_path in self._include:
            cp = commonpath([self._build_dir, file_path])
            relative_file_path = relpath(file_path, cp)

            if relative_file_path in result_contracts:
                continue

            file_name = Path(file_path).stem
            file_artifact_path: Path = self._build_dir.joinpath(
                relative_file_path
            ).joinpath(f"{file_name}.json")
            file_debug_path: Path = self._build_dir.joinpath(
                relative_file_path
            ).joinpath(f"{file_name}.dbg.json")
            if not file_artifact_path.exists() or not file_debug_path.exists():
                raise BuildArtifactsError("Could not find target artifacts")

            with file_artifact_path.open("r") as file:
                file_artifact = json.load(file)
            with file_debug_path.open("r") as file:
                file_debug_artifact = json.load(file)
            build_info_name = Path(file_debug_artifact["buildInfo"]).name
            with self._build_dir.joinpath(f"build-info/{build_info_name}").open(
                "r"
            ) as file:
                build_info = json.load(file)

            result_contracts[relative_file_path] = []

            contracts = build_info["output"]["contracts"][relative_file_path]

            for contract, data in contracts.items():
                if data["evm"]["bytecode"]["object"] == "":
                    continue
                result_contracts[relative_file_path] += [
                    {
                        "sourcePaths": {
                            i: k
                            for i, k in enumerate(
                                build_info["output"]["contracts"].keys()
                            )
                        },
                        "deployedSourceMap": data["evm"]["deployedBytecode"][
                            "sourceMap"
                        ],
                        "deployedBytecode": data["evm"]["deployedBytecode"]["object"],
                        "sourceMap": data["evm"]["bytecode"]["sourceMap"],
                        "bytecode": data["evm"]["bytecode"]["object"],
                        "contractName": file_artifact["contractName"],
                        "mainSourceFile": file_artifact["sourceName"],
                    }
                ]

            for source_file_dep, data in build_info["output"]["sources"].items():
                if source_file_dep in result_sources.keys():
                    continue

                result_sources[source_file_dep] = {
                    "fileIndex": data["id"],
                    "source": build_info["input"]["sources"][source_file_dep][
                        "content"
                    ],
                    "ast": data["ast"],
                }

        return result_contracts, result_sources


class HardhatJob:
    def __init__(self, target: List[str], build_dir: Path):
        artifacts = HardhatArtifacts(build_dir, targets=target)
        self._jb = JobBuilder(artifacts)
        self.payload = None

    def generate_payload(self):
        self.payload = self._jb.payload()
