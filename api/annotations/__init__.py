import json
import os


def get_title_func_mappings():
    # loading in mappings
    dir_path = os.path.dirname(os.path.realpath(__file__))

    with open(dir_path + "/static/data/title_func_mappings.json") as fh:
        title_func_mappings = json.load(fh)

    return title_func_mappings


TITLE_FUNC_MAPPINGS = get_title_func_mappings()
