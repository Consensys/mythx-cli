import click


def get_source_location_by_offset(source, offset):
    """Retrieve the Solidity source code location based on the source map offset.
    :param source: The Solidity source to analyze
    :param offset: The source map's offset
    :return: The line number
    """

    overall = 0
    line_ctr = 0
    for line in source.split("\n"):
        line_ctr += 1
        overall += len(line)
        if overall >= offset:
            return line_ctr
    raise click.exceptions.ClickException(
        "Error finding the source location for offset {} - max overall {} reached".format(offset, overall)
    )
