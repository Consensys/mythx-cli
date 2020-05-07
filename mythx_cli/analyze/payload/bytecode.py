"""This module contains functions to generate bytecode-only analysis request
payloads."""

from typing import Dict


def generate_bytecode_payload(code: str) -> Dict[str, str]:
    """Generate a payload containing only the creation bytecode.

    :param code: The creation bytecode as hex string starting with :code:`0x`
    :return: The payload dictionary to be sent to MythX
    """

    return {"bytecode": code}
