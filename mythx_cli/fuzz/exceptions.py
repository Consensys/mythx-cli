#
# FaaS Client Errors
#


class FaaSError(Exception):
    """Base class for FaaS module exceptions"""

    def __init__(self, message, detail=None):
        self.message = message
        self.detail = detail

    pass


# HTTP Requests


class RequestError(FaaSError):
    """Exception raised for errors with the http connection to the faas"""

    pass


class BadStatusCode(RequestError):
    """Exception raised for http responses with a bad status code"""

    pass


# Data Formats


class PayloadError(FaaSError):
    """Exception raised for errors extracting data from the provided payload"""

    pass


class ScribbleMetaError(FaaSError):
    """Exception raised for errors getting the Scribble Metadata"""

    pass


class CreateFaaSCampaignError(FaaSError):
    """Exception raised for errors creating the FaaS Campaign"""

    pass


#
# Brownie Job Errors
#


class BrownieError(Exception):
    """Base class for Brownie Job exceptions"""

    def __init__(self, message):
        self.message = message

    pass


class BuildArtifactsError(BrownieError):
    """Exception raised for errors fetching the build artifacts"""

    pass


class SourceError(BrownieError):
    """Exception raised for errors the source and AST of a source file"""

    pass


class PayloadError(BrownieError):
    """Exception raised for errors assembling the FaaS payload"""

    pass


#
# RPC client
#


class RPCCallError(FaaSError):
    """Exception raised when there is an error calling the RPC endpoint"""

    pass


class SeedStateError(FaaSError):
    """Exception raised when there is an error generating the seed state"""

    pass
