import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict

from mythx_cli.fuzz.exceptions import BuildArtifactsError


class IDEArtifacts(ABC):
    @property
    @abstractmethod
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
    @abstractmethod
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

    @staticmethod
    def _get_build_artifacts(build_dir) -> Dict:
        build_files_by_source_file = {}

        build_dir = Path(build_dir)

        if not build_dir.is_dir():
            raise BuildArtifactsError("Build directory doesn't exist")

        for child in build_dir.glob("**/*"):
            if not child.is_file():
                continue
            if not child.name.endswith(".json"):
                continue

            data = json.loads(child.read_text("utf-8"))

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
        contracts = [
            c
            for contracts_for_file in self._artifacts.contracts.values()
            for c in contracts_for_file
        ]
        return {"contracts": contracts, "sources": sources}
