#!/usr/bin/env python
import argparse
import os
import subprocess
import warnings
import multiprocessing


def get_default_processes():
    """Get default number of processes (n_threads - 1)."""
    return max(1, multiprocessing.cpu_count() - 1)


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="CarveMe wrapper for metabolic model reconstruction using input files."
    )
    # Convert --input to positional argument
    parser.add_argument(
        "input",
        help="Path to TSV input file with columns: genome, universe, media_file, medium_id",
    )
    parser.add_argument(
        "-o",
        "--output",
        required=True,
        help="Output folder for generated models",
    )
    # TSV flag for parallel processing
    parser.add_argument(
        "--tsv",
        action="store_true",
        help="Interpret input file as a TSV file with columns: genome, universe, media_file, medium_id",
    )
    # Add back processes argument with smart default
    parser.add_argument(
        "-p",
        "--processes",
        type=int,
        default=get_default_processes(),
        help=f"Number of processes to use for parallel genome processing (default: {get_default_processes()})",
    )

    # Rest of arguments remain the same
    input_type_args = parser.add_mutually_exclusive_group()
    input_type_args.add_argument(
        "--dna", action="store_true", help="Build from DNA fasta file"
    )
    input_type_args.add_argument(
        "--egg", action="store_true", help="Build from eggNOG-mapper output file"
    )
    input_type_args.add_argument(
        "--diamond", action="store_true", help=argparse.SUPPRESS
    )
    input_type_args.add_argument(
        "--refseq",
        action="store_true",
        help="Download genome from NCBI RefSeq and build",
    )

    parser.add_argument(
        "--diamond-args", help="Additional arguments for running diamond"
    )
    sbml = parser.add_mutually_exclusive_group()
    sbml.add_argument(
        "--cobra", action="store_true", help="Output SBML in old cobra format"
    )
    sbml.add_argument(
        "--fbc2", action="store_true", help="Output SBML in sbml-fbc2 format"
    )
    parser.add_argument(
        "-n", "--ensemble", type=int, help="Build model ensemble with N models"
    )
    parser.add_argument("--soft", help="Soft constraints file")
    parser.add_argument("--hard", help="Hard constraints file")
    parser.add_argument(
        "--reference", help="Manually curated model of a close reference species"
    )
    parser.add_argument(
        "--solver",
        default="scip",
        help="Select MILP solver. Available options: cplex, gurobi, scip [default]",
    )
    parser.add_argument(
        "--default-score", type=float, default=-1.0, help=argparse.SUPPRESS
    )
    parser.add_argument(
        "--uptake-score", type=float, default=0.0, help=argparse.SUPPRESS
    )
    parser.add_argument("--soft-score", type=float, default=1.0, help=argparse.SUPPRESS)
    parser.add_argument(
        "--reference-score", type=float, default=0.0, help=argparse.SUPPRESS
    )
    parser.add_argument("--blind-gapfill", action="store_true", help=argparse.SUPPRESS)

    return parser.parse_args()


def build_carve_command(args) -> list:
    """Build the CarveMe command with all specified arguments."""
    # Changed to use positional input argument
    cmd = ["carve", args.input, "-o", args.output]

    # Add TSV flag if provided along with processes
    if args.tsv:
        cmd.append("--tsv")
        # Only add processes argument when using TSV mode
        cmd.extend(["--processes", str(args.processes)])

    # Add solver selection
    cmd.extend(["--solver", args.solver])

    # Rest of the command building remains the same
    if args.dna:
        cmd.append("--dna")
    elif args.egg:
        cmd.append("--egg")
    elif args.diamond:
        cmd.append("--diamond")
    elif args.refseq:
        cmd.append("--refseq")

    if args.diamond_args:
        cmd.extend(["--diamond-args", args.diamond_args])

    if args.cobra:
        cmd.append("--cobra")
    elif args.fbc2:
        cmd.append("--fbc2")

    if args.ensemble:
        cmd.extend(["-n", str(args.ensemble)])

    if args.soft:
        cmd.extend(["--soft", args.soft])
    if args.hard:
        cmd.extend(["--hard", args.hard])
    if args.reference:
        cmd.extend(["--reference", args.reference])

    if args.default_score != -1.0:
        cmd.extend(["--default-score", str(args.default_score)])
    if args.uptake_score != 0.0:
        cmd.extend(["--uptake-score", str(args.uptake_score)])
    if args.soft_score != 1.0:
        cmd.extend(["--soft-score", str(args.soft_score)])
    if args.reference_score != 0.0:
        cmd.extend(["--reference-score", str(args.reference_score)])
    if args.blind_gapfill:
        cmd.append("--blind-gapfill")

    return cmd


def main() -> None:
    """Main function."""
    warnings.filterwarnings("ignore", module="pyscipopt")
    try:
        args = parse_arguments()

        # Create output directory if it doesn't exist
        os.makedirs(args.output, exist_ok=True)

        # Build and run CarveMe command
        carve_command = build_carve_command(args)

        print("Running CarveMe with command:")
        print(" ".join(carve_command))

        subprocess.run(carve_command, check=True)
        print("CarveMe processing completed successfully")

    except subprocess.CalledProcessError as e:
        print(f"CarveMe execution failed: {str(e)}")
        exit(1)
    except Exception as e:
        print(f"Error: {str(e)}")
        exit(1)


if __name__ == "__main__":
    main()
