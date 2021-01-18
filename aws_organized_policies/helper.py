import regex as re
import yaml
import json
import os
from pathlib import Path

SEP = os.path.sep


def get_valid_filename(s):
    """
    https://github.com/django/django/blob/master/django/utils/text.py
    Return the given string converted to a string that can be used for a clean
    filename. Remove leading and trailing spaces; convert other spaces to
    underscores; and remove anything that is not an alphanumeric, dash,
    underscore, or dot.
    >>> get_valid_filename("john's portrait in 2004.jpg")
    'johns_portrait_in_2004.jpg'
    """
    s = str(s).strip().replace(" ", "_")
    return re.sub(r"(?u)[^-\w]", "", s)


def getListOfFiles(dirName) -> list:
    # create a list of file and sub directories
    # names in the given directory
    listOfFile = os.listdir(dirName)
    allFiles = list()
    # Iterate over all the entries
    for entry in listOfFile:
        # Create full path
        fullPath = os.path.join(dirName, entry)
        # If entry is a directory then get the list of files in this directory
        if os.path.isdir(fullPath):
            allFiles = allFiles + getListOfFiles(fullPath)
        else:
            # Make sure only non empty entries are saved
            if not entry.startswith("."):
                allFiles.append(fullPath)
    return allFiles


# file path structure  ===> _organizational_units/_accounts ->  name -> meta
# ==> indexes: -2/-1/0
def map_scp_path_for_target_name(file_list, root_id) -> dict:
    # organizational_units_path = dict()
    # accounts_path = dict()
    # accounts_path[root_id] = "environment/" + root_id
    # organizational_units_path['Root'] = "environment/" + root_id

    scp_path_to_target = dict()
    scp_path_to_target[root_id] = "environment/" + root_id
    scp_path_to_target["Root"] = "environment/" + root_id

    for path in file_list:
        path_list = path.split("/")[:-1]
        name = path_list[-1]
        target_type = path_list[-2]

        scp_path_to_target[name] = SEP.join(path_list)

        if target_type == "_accounts" or target_type == "_organizational_units":
            scp_path_to_target[name] = SEP.join(path_list)

        # elif target_type == "_organizational_units":
        #     organizational_units_path[name] = SEP.join(path_list)

    return scp_path_to_target


def read_yaml(file_path):
    with open(file_path, "r") as stream:
        try:
            return yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
            return None


def write_to_file(data, path, file_name) -> None:
    Path(path).mkdir(parents=True, exist_ok=True)
    if ".yaml" in file_name:
        with open(SEP.join([path, file_name]), "w") as outfile:
            yaml.dump(data, outfile, default_flow_style=False)
    elif ".json" in file_name:
        with open(SEP.join([path, file_name]), "w") as outfile:
            json.dump(data, outfile, indent=4)


def write_inherited_yaml(data, path) -> None:
    with open(path, "r") as yamlfile:
        cur_yaml = yaml.safe_load(yamlfile)["Policies_Attached"]  # Note the safe_load
    if cur_yaml:
        with open(path, "w") as yamlfile:
            yaml.safe_dump(
                {"Policies_Inherited": data} | {"Policies_Attached": cur_yaml}, yamlfile
            )  # Also note the safe_dump
