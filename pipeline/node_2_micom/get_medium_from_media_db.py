import pandas as pd
import argparse


def get_medium_from_media_db(
    media_db: str,
    medium_id: str,
    compartment: str = "e",
    max_uptake: float = 1000,
    outfile: str = None,
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


def main():
    """Entry point of the script."""
    parser = argparse.ArgumentParser(
        description="Extract exchange reactions for a given medium from a media database."
    )
    parser.add_argument(
        "--media-db", type=str, required=True, help="Path to the media database."
    )
    parser.add_argument(
        "--medium-id", type=str, required=True, help="ID of the medium to use."
    )
    parser.add_argument(
        "--compartment",
        type=str,
        default="e",
        help="Compartment of exchanges. Defaults to 'e'.",
    )
    parser.add_argument(
        "--max-uptake",
        type=float,
        default=1000,
        help="Maximum uptake rate. Defaults to 1000.",
    )
    parser.add_argument(
        "--outfile", type=str, help="Path to write the extracted medium to. Optional."
    )

    args = parser.parse_args()

    get_medium_from_media_db(
        media_db=args.media_db,
        medium_id=args.medium_id,
        compartment=args.compartment,
        max_uptake=args.max_uptake,
        outfile=args.outfile,
    )


if __name__ == "__main__":
    main()
