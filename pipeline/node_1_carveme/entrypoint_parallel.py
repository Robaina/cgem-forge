#!/usr/bin/env python
import argparse
import os
import subprocess
from multiprocessing import Pool
from typing import Dict, List, Union, Tuple
import sys
import pandas as pd


def read_config_file(config_file: str) -> pd.DataFrame:
    """
    Read and validate the configuration TSV file.

    Expected columns: genome, universe, media_file, medium_id

    Args:
        config_file: Path to the TSV configuration file

    Returns:
        DataFrame containing the validated configuration
    """
    try:
        config = pd.read_csv(config_file, sep="\t")
        required_columns = ["genome", "universe", "media_file", "medium_id"]

        # Check for required columns
        missing_cols = set(required_columns) - set(config.columns)
        if missing_cols:
            print(f"Error: Missing required columns in config file: {missing_cols}")
            sys.exit(1)

        # Validate file existence
        for col in ["genome", "universe", "media_file"]:
            invalid_files = [f for f in config[col] if not os.path.isfile(f)]
            if invalid_files:
                print(f"Error: Following {col} files not found:")
                for f in invalid_files:
                    print(f"  - {f}")
                sys.exit(1)

        return config

    except Exception as e:
        print(f"Error reading config file: {str(e)}")
        sys.exit(1)


def validate_input_files(
    genomes: Union[str, List[str]],
    universe_files: Union[str, List[str]],
    media_file: str,
    medium_id: str,
) -> Tuple[List[str], Dict[str, Dict[str, str]]]:
    """
    Validate input files and create parameter mapping.
    """
    try:
        # Convert single inputs to lists
        genome_files = [genomes] if isinstance(genomes, str) else genomes
        universe_files = (
            [universe_files] if isinstance(universe_files, str) else universe_files
        )

        # Validate all files exist
        for genome in genome_files:
            if not os.path.isfile(genome):
                print(f"Error: Genome file {genome} not found")
                sys.exit(1)

        if len(universe_files) == 1:
            universe_files = universe_files * len(genome_files)
        elif len(universe_files) != len(genome_files):
            print(
                f"Error: Number of universe files ({len(universe_files)}) "
                f"does not match number of genome files ({len(genome_files)})"
            )
            sys.exit(1)

        # Create parameter mapping
        params_map = {}
        for genome, universe in zip(genome_files, universe_files):
            params_map[genome] = {
                "genome": genome,
                "universe": universe,
                "media_file": media_file,
                "medium_id": medium_id,
            }

        return genome_files, params_map
    except Exception as e:
        print(f"Error validating input files: {str(e)}")
        sys.exit(1)


def carve_genome(args: tuple) -> None:
    """
    Process a single genome file with CarveMe.

    Args:
        args: Tuple containing (genome_path, genome_params, outdir)
    """
    try:
        genome_path, genome_params, outdir = args
        output_file = os.path.join(
            outdir,
            f"{os.path.splitext(os.path.basename(genome_path))[0]}.xml",
        )

        carve_command = [
            "carve",
            "--solver",
            "scip",
            "-o",
            output_file,
            "--universe-file",
            genome_params["universe"],
            "--init",
            genome_params["medium_id"],
            "--gapfill",
            genome_params["medium_id"],
            "--mediadb",
            genome_params["media_file"],
            genome_path,
        ]

        # Debug info
        print(f"\nProcessing {os.path.basename(genome_path)}")
        print(f"  Universe: {genome_params['universe']}")
        print(f"  Media: {genome_params['media_file']}")
        print(f"  Medium ID: {genome_params['medium_id']}")

        subprocess.run(carve_command, check=True)
        print(f"Completed processing {os.path.basename(genome_path)}")
        return output_file

    except Exception as e:
        print(f"Error processing {os.path.basename(genome_path)}: {str(e)}")
        raise


def carve_genomes(
    genome_params: Dict[str, Dict[str, str]], outdir: str, num_processes: int = None
) -> None:
    """
    Execute carve commands in parallel for all input files using multiprocessing Pool.
    """
    try:
        os.makedirs(outdir, exist_ok=True)

        # Prepare arguments for multiprocessing
        process_args = [
            (genome_file, params, outdir)
            for genome_file, params in genome_params.items()
        ]

        # Create pool and process genomes in parallel
        with Pool(processes=num_processes) as pool:
            results = pool.map(carve_genome, process_args)

        print(f"\nProcessed {len(results)} genomes successfully")

    except Exception as e:
        print(f"Error in carve_genomes: {str(e)}")
        sys.exit(1)


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    try:
        parser = argparse.ArgumentParser(
            description="Parallel CarveMe processing for metabolic model reconstruction."
        )

        # Add config file option
        parser.add_argument(
            "--config",
            help="Path to TSV configuration file with columns: genome, universe, media_file, medium_id",
        )

        # Original arguments
        parser.add_argument(
            "--genomes", nargs="+", help="Path(s) to input genome file(s)"
        )
        parser.add_argument("--media_file", help="Path to the media file")
        parser.add_argument("--medium_id", help="ID of the medium")
        parser.add_argument(
            "--universe_file",
            nargs="+",
            help="Path to universe file(s). If single file, will be used for all genomes",
        )
        parser.add_argument(
            "--outdir", default="./results", help="Directory to save output XML files"
        )
        parser.add_argument(
            "--processes",
            type=int,
            default=None,
            help="Number of parallel processes (default: CPU count)",
        )

        args = parser.parse_args()

        # Validate that either config file or all required arguments are provided
        if args.config is None and (
            args.genomes is None
            or args.media_file is None
            or args.medium_id is None
            or args.universe_file is None
        ):
            parser.error(
                "Either --config or all of --genomes, --media_file, --medium_id, "
                "and --universe_file must be provided"
            )

        return args
    except Exception as e:
        print(f"Error parsing arguments: {str(e)}")
        sys.exit(1)


def main() -> None:
    """Main function."""
    try:
        args = parse_arguments()

        if args.config:
            # Use config file
            config = read_config_file(args.config)
            genome_files = config["genome"].tolist()
            genome_params = {}
            for _, row in config.iterrows():
                genome_params[row["genome"]] = {
                    "genome": row["genome"],
                    "universe": row["universe"],
                    "media_file": row["media_file"],
                    "medium_id": row["medium_id"],
                }
        else:
            # Use command line arguments
            _, genome_params = validate_input_files(
                args.genomes,
                (
                    args.universe_file[0]
                    if len(args.universe_file) == 1
                    else args.universe_file
                ),
                args.media_file,
                args.medium_id,
            )

        carve_genomes(genome_params, args.outdir, args.processes)

    except Exception as e:
        print(f"Error in main: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
