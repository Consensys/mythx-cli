import json
import logging
import random
import string

import click
import requests

from mythx_cli.analyze.scribble import ScribbleMixin

from .exceptions import (
    BadStatusCode,
    CreateFaaSCampaignError,
    PayloadError,
    RequestError,
    ScribbleMetaError,
)

LOGGER = logging.getLogger("mythx-cli")

headers = {"Content-Type": "application/json"}


class FaasClient:
    """ A client to interact with the FaaS API.

    This object receives solidity compilation artifacts and a Harvey Seed state, generates a payload that the faas
    API can consume and submits it, also triggering the start of a Campaign.
    """

    def __init__(self, faas_url, campaign_name_prefix, project_type):
        self.faas_url = faas_url
        self.campaign_name_prefix = campaign_name_prefix
        self.project_type = project_type

    def generate_campaign_name(self):
        """Return a random name with the provided prefix self.campaign_name_prefix."""
        letters = string.ascii_lowercase
        random_string = "".join(random.choice(letters) for i in range(5))
        return str(self.campaign_name_prefix + "_" + random_string)

    def start_faas_campaign(self, payload):
        """Make HTTP request to the faas"""
        try:
            req_url = f"{self.faas_url}/api/campaigns?start_immediately=true"
            response = requests.post(req_url, json=payload, headers=headers)
            response_data = response.json()
            if response.status_code != requests.codes.ok:
                raise BadStatusCode(
                    f"Got http status code {response.status_code} for request {req_url}"
                )
            return response_data["id"]
        except Exception as e:
            raise RequestError(f"Error starting FaaS campaign.")

    def create_faas_campaign(self, campaign_data, seed_state):
        """Submit a campaign to the FaaS and start that campaign.

        This function takes a FaaS payload and makes an HTTP request to the Faas backend, which
        then creates and starts a campaign. The campaign is started because of the `start_immediately=true` query
        parameter.

        This will send the following data to the FaaS for analysis:

        * :code:`name`
        * :code:`parameters` A dict of Harvey configuration options
        * :code:`sources` A dict containing source files code and AST
        * :code:`contracts` Solidity artifacts of the target smart contracts
        * :code:`corpus` Seed state of the target contract. Usually the list of transactions that took place on the
        local ganache (or equivalent) instance.

        :return: Campaign ID
        """
        try:
            if self.project_type != "brownie":
                raise click.exceptions.UsageError(
                    "Currently only Brownie projects are supported"
                )

            try:
                api_payload = {"parameters": {}}
                api_payload["name"] = self.generate_campaign_name()
                api_payload["parameters"][
                    "discovery-probability-threshold"
                ] = seed_state["discovery-probability-threshold"]
                api_payload["parameters"]["num-cores"] = seed_state["num-cores"]
                api_payload["parameters"]["assertion-checking-mode"] = seed_state[
                    "assertion-checking-mode"
                ]
                api_payload["corpus"] = seed_state["analysis-setup"]
                api_payload["sources"] = campaign_data.payload["sources"]
                api_payload["contracts"] = campaign_data.payload["contracts"]
            except Exception:
                raise PayloadError(f"Error extracting data from payload")

            try:
                instr_meta = ScribbleMixin.get_arming_instr_meta()

                if instr_meta is not None:
                    api_payload["instrumentation_metadata"] = instr_meta
            except Exception as e:
                raise ScribbleMetaError(
                    f"Error getting Scribble arming metadata."
                ) from e

            campaign_id = self.start_faas_campaign(api_payload)

            return campaign_id
        except (PayloadError, ScribbleMetaError) as e:
            raise CreateFaaSCampaignError(f"Error creating the FaaS campaign:")
