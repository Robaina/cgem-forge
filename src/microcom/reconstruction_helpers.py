import re
import json
from pathlib import Path

import pandas as pd


def remove_compartment(met_id: str) -> str:
    return re.sub(r"_[a-z]$", "", met_id)


def extract_chemical_elements(formula: str) -> dict:
    """
    Extract the chemical components from a chemical formula.
    """
    components = re.findall(r"([A-Z][a-z]*)(\d*)", formula)
    component_dict = {}
    for element, count in components:
        component_dict[element] = int(count) if count else 1
    return component_dict


def is_co2(chemical_elements: dict) -> bool:
    """Check whether molecule is CO2.

    Args:
        chemical_elements (dict): dictionary of chemical elements

    Returns:
        bool: True if CO2, False otherwise
    """
    return chemical_elements == {"C": 1, "O": 2}


def is_hco3(chemical_elements: dict) -> bool:
    """Check whether molecule is HCO3-.

    Args:
        chemical_elements (dict): dictionary of chemical elements

    Returns:
        bool: True if HCO3-, False otherwise
    """
    return chemical_elements == {"C": 1, "H": 1, "O": 3}


def get_medium_dict_from_media_db(media_db: Path, medium_id: str) -> dict:
    """
    Get a dictionary of exchange reactions for a given medium.

    Args:
        model (Model): _description_
        media_db (Path): _description_
        medium_id (str): _description_

    Returns:
        Model: _description_
    """
    media = pd.read_csv(media_db, sep="\t")
    if medium_id not in media.medium.values:
        raise ValueError(f"Medium {medium_id} not found in media database.")
    return {
        f"EX_{species}_e": 1000
        for species in media[media["medium"] == medium_id].compound
    }


def get_dict_of_metabolite_ids(BIGG_metabolites_json: Path) -> dict:
    """
    Get a dictionary of metabolite IDs and names from the BIGG metabolites JSON file.
    Args:
        BIGG_metabolites_json (Path): _description_

    Returns:
        dict: _description_
    """
    with open(BIGG_metabolites_json, "r") as f:
        met_data = json.load(f)
    met_names = {}
    for entry in met_data["results"]:
        met_names[entry["bigg_id"]] = entry["name"]
    return met_names


def assign_name_to_met_id(met_names: dict, met_id: str) -> str:
    """
    Assign a name to a metabolite ID.
    """
    met_id = met_id.split("_")[1]
    if met_id in met_names:
        return met_names[met_id]
    else:
        return met_id
