import re
from copy import copy


def zero_srcmap_indices(src_map: str) -> str:
    """Zero the source map file index entries.

    :param src_map: The source map string to process
    :return: The processed source map string
    """
    entries = src_map.split(";")
    new_entries = copy(entries)
    for i, entry in enumerate(entries):
        fields = entry.split(":")
        if len(fields) > 2 and fields[2] not in ("-1", ""):
            # file index is in entry, needs fixing
            fields[2] = "0"
            new_entries[i] = ":".join(fields)
    return ";".join(new_entries)


def patch_solc_bytecode(code: str) -> str:
    """Patch solc bytecode placeholders.

    This function patches placeholders in solc output. These placeholders are meant
    to be replaced with deployed library/dependency addresses on deployment, but do not form
    valid EVM bytecode. To produce a valid payload, placeholders are replaced with the zero-address.

    :param code: The bytecode to patch
    :return: The patched bytecode with the zero-address filled in
    """
    return re.sub(re.compile(r"__\$.{34}\$__"), "0" * 40, code)


def patch_truffle_bytecode(code: str) -> str:
    """Patch Truffle bytecode placeholders.

    This function patches placeholders in Truffle artifact files. These placeholders are meant
    to be replaced with deployed library/dependency addresses on deployment, but do not form
    valid EVM bytecode. To produce a valid payload, placeholders are replaced with the zero-address.

    :param code: The bytecode to patch
    :return: The patched bytecode with the zero-address filled in
    """
    return re.sub(re.compile(r"__\w{38}"), "0" * 40, code)
