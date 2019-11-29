from pathlib import Path
import json


def get_test_case(path: str, obj=None, raw=False):
    with open(str(Path(__file__).parent / path)) as f:
        if raw:
            return f.read()
        dict_data = json.load(f)

    if obj is None:
        return dict_data
    return obj.from_dict(dict_data)
