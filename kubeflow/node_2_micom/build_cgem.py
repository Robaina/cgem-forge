import argparse
import pandas as pd
from micom.workflows import build


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Build MICOM models from taxonomy data."
    )
    parser.add_argument(
        "--taxa_table", type=str, help="Path to the MICOM database TSV file."
    )
    parser.add_argument(
        "--outdir",
        type=str,
        default="results/micom",
        help="Output folder for results.",
    )
    parser.add_argument(
        "--abundance_cutoff",
        type=float,
        default=1e-2,
        help="Cutoff value for the build process.",
    )
    parser.add_argument(
        "--threads", type=int, default=2, help="Number of threads to use."
    )
    parser.add_argument(
        "--solver", type=str, default="gurobi", help="Solver to use for optimization."
    )
    return parser.parse_args()


def build_models(
    data_file: str, out_folder: str, cutoff: float, threads: int, solver: str
):
    taxo_df = pd.read_csv(data_file, sep="\t", index_col=None)
    manifest = build(
        taxonomy=taxo_df,
        model_db=None,
        out_folder=out_folder,
        cutoff=cutoff,
        threads=threads,
        solver=solver,
    )
    return manifest


def main():
    args = parse_arguments()
    manifest = build_models(
        args.taxa_table, args.outdir, args.abundance_cutoff, args.threads, args.solver
    )
    print("Model building completed. Manifest:")
    print(manifest)


if __name__ == "__main__":
    main()
