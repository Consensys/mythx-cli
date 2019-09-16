"""Utility functions for handling API requests and responses."""


def get_source_location_by_offset(source, offset):
    """Retrieve the Solidity source code location based on the source map offset.

    :param source: The Solidity source to analyze
    :param offset: The source map's offset
    :return: The line number
    """

    return source.encode("utf-8")[0:offset].count("\n".encode("utf-8")) + 1
