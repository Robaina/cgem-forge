#!/usr/bin/env python
import argparse
import glob
import os
import subprocess


def run_smetana(
    models_pattern: str,
    media: str,
    mediadb: str,
    outdir: str,
    solver: str,
    detailed: bool,
) -> None:
    """
    Executes the smetana command with the specified parameters.

    Args:
        models_pattern: Pattern for model XML files to include in the analysis.
        media: Definition of the media to use.
        mediadb: Path to the media database file.
        outdir: Directory where the output will be saved.
        solver: Solver to use for the analysis.
        detailed: Flag to produce detailed output.
    """
    # Ensure output directory exists
    os.makedirs(outdir, exist_ok=True)

    # Find model files matching the pattern
    model_files = glob.glob(models_pattern)

    # Construct the smetana command
    smetana_command = (
        ["smetana"]
        + model_files
        + ["-m", media, "--mediadb", mediadb, "-o", outdir, "--solver", solver]
    )

    if detailed:
        smetana_command.append("--detailed")

    # Execute the smetana command
    subprocess.run(smetana_command, check=True)


def parse_arguments() -> argparse.Namespace:
    """
    Parses command-line arguments.

    Returns:
        Namespace containing the parsed arguments.
    """
    parser = argparse.ArgumentParser(
        description="Entry point script for executing the smetana command in a Docker container."
    )

    parser.add_argument(
        "--models-pattern",
        required=True,
        help="Pattern for model XML files to include in the analysis.",
    )
    parser.add_argument(
        "--media", required=True, help="Definition of the media to use."
    )
    parser.add_argument(
        "--mediadb", required=True, help="Path to the media database file."
    )
    parser.add_argument(
        "--outdir", required=True, help="Directory where the output will be saved."
    )
    parser.add_argument(
        "--solver", default="gurobi", help="Solver to use for the analysis."
    )
    parser.add_argument(
        "--detailed", action="store_true", help="Produce detailed output."
    )

    return parser.parse_args()


def main() -> None:
    """
    Main function to parse arguments and execute the smetana command.
    """
    args = parse_arguments()
    run_smetana(
        args.models_pattern,
        args.media,
        args.mediadb,
        args.outdir,
        args.solver,
        args.detailed,
    )


if __name__ == "__main__":
    main()
