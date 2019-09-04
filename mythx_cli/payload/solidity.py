def generate_solidity_payload(file):
    with open(file) as f:
        source = f.read()
    # TODO: Compile with py-solc-x
    return {"sources": {file: {"source": source}}, "source_list": [file]}
