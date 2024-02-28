#!/usr/bin/env python
import argparse
import os
import subprocess


def carve_genomes(
    genomes_dir: str, media_file: str, medium_id: str, universe_file: str, outdir: str
) -> None:
    """
    Executes the carve command for each input file in the specified genomes directory,
    assuming all files are relevant input files for the metabolic model reconstruction
    process. This approach is particularly suited for processing directories containing
    protein sequences in .faa format or any other relevant formats present.

    Args:
        genomes_dir: Directory containing input faa files for model reconstruction.
        media_file: Path to the media file.
        medium_id: ID of the medium to use for initialization and gap-filling.
        universe_file: Path to the universe file.
        outdir: Directory where output XML files will be saved.
    """
    # Ensure output directory exists
    os.makedirs(outdir, exist_ok=True)

    # List all files in the genomes directory (without filtering by extension)
    input_files = os.listdir(genomes_dir)

    for file in input_files:
        output_file = os.path.join(outdir, f"{os.path.splitext(file)[0]}.xml")
        file_path = os.path.join(genomes_dir, file)

        # Construct the carve command
        carve_command = [
            "carve",
            "--solver",
            "scip",
            "-o",
            output_file,
            "--universe-file",
            universe_file,
            "--init",
            medium_id,
            "--gapfill",
            medium_id,
            "--mediadb",
            media_file,
            file_path,
        ]

        # Execute the carve command
        subprocess.run(carve_command, check=True)


def parse_arguments() -> argparse.Namespace:
    """
    Parses command-line arguments.

    Returns:
        Namespace containing the parsed arguments.
    """
    parser = argparse.ArgumentParser(
        description="CarveMe Docker container entry point script for processing protein sequences."
    )

    parser.add_argument(
        "--genomes-dir",
        required=True,
        help="Directory containing input faa files for model reconstruction.",
    )
    parser.add_argument("--media-file", required=True, help="Path to the media file.")
    parser.add_argument("--medium-id", required=True, help="ID of the medium.")
    parser.add_argument(
        "--universe-file", required=True, help="Path to the universe file."
    )
    parser.add_argument(
        "--outdir", default="./results", help="Directory to save the output XML files."
    )

    return parser.parse_args()


def main() -> None:
    """
    Main function to parse arguments and execute the carve command on all input files
    in the specified directory.
    """
    args = parse_arguments()
    carve_genomes(
        args.genomes_dir,
        args.media_file,
        args.medium_id,
        args.universe_file,
        args.outdir,
    )


if __name__ == "__main__":
    main()
