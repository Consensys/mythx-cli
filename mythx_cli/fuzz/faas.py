import logging
import random
from mythx_cli.analyze.scribble import ScribbleMixin
import click
import requests
import json
import string

LOGGER = logging.getLogger("mythx-cli")

headers = {
    'Content-Type': 'application/json'
}


class FaasClient():
    def __init__(self, faas_url, campaign_name_prefix, project_type):
        self.faas_url = faas_url
        self.campaign_name_prefix = campaign_name_prefix
        self.project_type = project_type

    def generate_campaign_name(self):
        """Generates a random campaign name, starting with the provided
        campaign name prefix, followed by 5 random characters, ensuring
        each campaign has a unique name.
        """
        letters = string.ascii_lowercase
        random_string = ''.join(random.choice(letters) for i in range(5))
        return str(self.campaign_name_prefix + "_" + random_string)

    def start_faas_campaign(self, payload):
        response = (requests.request("POST", self.faas_url + "/api/campaigns?start_immediately=true", headers=headers,
                                     data=payload)).json()
        return response["id"]

    def create_faas_campaign(self, campaign_data, seed_state):
        """ A FaaS campaign creation request requires 3 fields:
            - sources: dictionary of source code and AST of source files, indexed by file name
            - corpus: Harvey's seed state
            - parameters: Harvey's configuration settings
            - contracts: contract build artifacts (bytecode, sourcemap, etc)
            For full docs visit {faas_url}/docs#operation/list_campaigns_api_campaigns__get
        """
        if self.project_type != 'brownie':
            raise click.exceptions.UsageError("Currently only Brownie projects are supported")

        api_payload = {"parameters": {}}
        api_payload["name"] = self.generate_campaign_name()
        api_payload["parameters"]["discovery-probability-threshold"] = seed_state["discovery-probability-threshold"]
        api_payload["parameters"]["num-cores"] = seed_state["num-cores"]
        api_payload["parameters"]["assertion-checking-mode"] = seed_state["assertion-checking-mode"]
        api_payload["corpus"] = seed_state["analysis-setup"]

        api_payload["sources"] = campaign_data.payload["sources"]
        api_payload["contracts"] = campaign_data.payload["contracts"]

        instr_meta = ScribbleMixin.get_arming_instr_meta()

        if instr_meta is not None:
            api_payload["instrumentation_metadata"] = instr_meta

        #print(json.dumps(api_payload))
        campaign_id = self.start_faas_campaign(json.dumps(api_payload))

        return campaign_id
