import argparse
from src.helper_functions import get_medium_from_media_db


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Create Medium file from Media Database"
    )
    parser.add_argument(
        "media_db_file", type=str, help="Path to the media database file"
    )
    parser.add_argument("medium_id", type=str, help="ID of the medium")
    parser.add_argument(
        "compartment",
        type=str,
        default="e",
        help="Compartment where exchanges take place",
    )
    parser.add_argument(
        "max_uptake", type=float, default=10.0, help="Maximum uptake value"
    )
    parser.add_argument("outfile", type=str, help="Output file path")
    return parser.parse_args()


def main(args):
    get_medium_from_media_db(
        args.media_db_file,
        args.medium_id,
        compartment=args.compartment,
        max_uptake=args.max_uptake,
        outfile=args.outfile,
    )


if __name__ == "__main__":
    args = parse_arguments()
    main(args)
