from abc import ABC, abstractmethod
from typing import Dict


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
