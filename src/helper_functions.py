from pathlib import Path
import pandas as pd


def get_medium_from_media_db(
    media_db: Path,
    medium_id: str,
    compartment: str = "e",
    max_uptake: float = 1000,
    outfile: Path = None,
) -> dict:
    """
    Get a dictionary of exchange reactions for a given medium.

    Args:
        media_db (Path): path to the media database
        medium_id (str): ID of the medium to use
        compartment (str, optional): compartment of exchanges. Defaults to "e".
        max_uptake (float, optional): maximum uptake rate. Defaults to 1000.
        outfile (Path, optional): path to write the extracted medium to. Defaults to None.

    Returns:
        medium (dict): dictionary containing exchange reactions and their maximum uptake rates
    """
    media = pd.read_csv(media_db, sep="\t")
    if medium_id not in media.medium.values:
        raise ValueError(f"Medium {medium_id} not found in media database.")
    medium = {
        f"EX_{species}_{compartment}": max_uptake
        for species in media[media["medium"] == medium_id].compound
    }
    if outfile is not None:
        with open(outfile, "w") as f:
            for k, v in medium.items():
                f.write(f"{k}\t{v}\n")
    return medium
