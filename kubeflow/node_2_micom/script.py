#!/usr/bin/env python

"""
This script serves as an entry point to execute various scripts used in a Nextflow pipeline for micom,
allowing the user to select a specific operation via subcommands.

Available subcommands:
- build_taxa_table: Builds a taxa table from abundances and genomes.
- build_cgem: Builds a community GEM.
- get_exchanges: Retrieves exchange reactions for a community GEM.
- get_elasticities: Calculates elasticities for a community GEM.

Usage:
    entry_script.py <subcommand> [options]
"""

import argparse
import subprocess


def build_taxa_table(args):
    """Builds a taxa table from abundances and genomes."""
    command = [
        "python",
        f"{args.scripts_dir}/build_taxa_table.py",
        args.sample_id,
        args.abundances,
        args.gems_dir,
        "--output",
        args.out_taxatable,
    ]
    subprocess.run(command, check=True)


def build_cgem(args):
    """Builds a community GEM."""
    command = [
        "python",
        f"{args.scripts_dir}/build_cgem.py",
        args.taxa_table,
        "--out_folder",
        args.outdir,
        "--cutoff",
        str(args.abundance_cutoff),
        "--threads",
        str(args.threads),
        "--solver",
        args.solver,
    ]
    subprocess.run(command, check=True)


def get_exchanges(args):
    """Retrieves exchange reactions for a community GEM."""
    command = [
        "python",
        f"{args.scripts_dir}/get_exchanges.py",
        args.manifest,
        args.outdir,
        args.media_file,
        "--tradeoff",
        str(args.growth_tradeoff),
        "--threads",
        str(args.threads),
        "--output",
        args.out_exchanges,
    ]
    subprocess.run(command, check=True)


def get_elasticities(args):
    """Calculates elasticities for a community GEM."""
    command = [
        "python",
        f"{args.scripts_dir}/get_elasticities.py",
        args.cgem_pickle,
        "--fraction",
        str(args.growth_tradeoff),
        "--output",
        args.out_elasticities,
    ]
    subprocess.run(command, check=True)


def main():
    parser = argparse.ArgumentParser(
        description="Entry point script for micom pipeline operations."
    )
    subparsers = parser.add_subparsers(help="Available commands")

    # Subcommand: build_taxa_table
    parser_taxa = subparsers.add_parser(
        "build_taxa_table", help="Builds a taxa table from abundances and genomes."
    )
    parser_taxa.add_argument("--sample_id", required=True, help="Sample ID.")
    parser_taxa.add_argument(
        "--abundances", required=True, help="Path to abundances file."
    )
    parser_taxa.add_argument(
        "--gems_dir", required=True, help="Directory containing genome files."
    )
    parser_taxa.add_argument(
        "--scripts_dir", required=True, help="Directory containing scripts."
    )
    parser_taxa.add_argument(
        "--out_taxatable", default="taxa_table.tsv", help="Output taxa table file."
    )
    parser_taxa.set_defaults(func=build_taxa_table)

    # Subcommand: build_cgem
    parser_cgem = subparsers.add_parser("build_cgem", help="Builds a community GEM.")
    parser_cgem.add_argument(
        "--taxa_table", required=True, help="Path to the taxa table file."
    )
    parser_cgem.add_argument(
        "--outdir", default="./results", help="Directory to save the output files."
    )
    parser_cgem.add_argument(
        "--abundance_cutoff",
        type=float,
        default=0.01,
        help="Abundance cutoff for including taxa.",
    )
    parser_cgem.add_argument(
        "--threads", type=int, default=10, help="Number of threads to use."
    )
    parser_cgem.add_argument(
        "--solver", default="gurobi", help="Solver to use for optimization."
    )
    parser_cgem.add_argument(
        "--scripts_dir", required=True, help="Directory containing scripts."
    )
    parser_cgem.set_defaults(func=build_cgem)

    # Subcommand: get_exchanges
    parser_exchanges = subparsers.add_parser(
        "get_exchanges", help="Retrieves exchange reactions for a community GEM."
    )
    parser_exchanges.add_argument(
        "--manifest", required=True, help="Path to the manifest file."
    )
    parser_exchanges.add_argument(
        "--outdir", required=True, help="Directory where the output will be saved."
    )
    parser_exchanges.add_argument(
        "--media_file", required=True, help="Path to the media file."
    )
    parser_exchanges.add_argument(
        "--growth_tradeoff", type=float, default=0.5, help="Growth tradeoff parameter."
    )
    parser_exchanges.add_argument(
        "--threads", type=int, default=10, help="Number of threads to use."
    )
    parser_exchanges.add_argument(
        "--out_exchanges",
        default="exchanges.tsv",
        help="Output file for exchange reactions.",
    )
    parser_exchanges.add_argument(
        "--scripts_dir", required=True, help="Directory containing scripts."
    )
    parser_exchanges.set_defaults(func=get_exchanges)

    # Subcommand: get_elasticities
    parser_elasticities = subparsers.add_parser(
        "get_elasticities", help="Calculates elasticities for a community GEM."
    )
    parser_elasticities.add_argument(
        "--cgem_pickle", required=True, help="Path to the community GEM pickle file."
    )
    parser_elasticities.add_argument(
        "--growth_tradeoff",
        type=float,
        default=0.5,
        help="Growth tradeoff parameter for elasticity calculation.",
    )
    parser_elasticities.add_argument(
        "--out_elasticities",
        default="elasticities.tsv",
        help="Output file for elasticities.",
    )
    parser_elasticities.add_argument(
        "--scripts_dir", required=True, help="Directory containing scripts."
    )
    parser_elasticities.set_defaults(func=get_elasticities)

    # Parse arguments and call the corresponding function
    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
