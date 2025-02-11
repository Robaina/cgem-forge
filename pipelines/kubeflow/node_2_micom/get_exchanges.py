import argparse
import pandas as pd
from micom.workflows import grow
from micom import load_pickle


def parse_arguments():
    parser = argparse.ArgumentParser(description="Run growth simulations using MICOM.")
    parser.add_argument("--manifest", type=str, help="Path to the manifest csv file.")
    parser.add_argument(
        "--outdir", type=str, help="Folder containing the MICOM community model."
    )
    parser.add_argument("--media_file", type=str, help="Path to the medium file.")
    parser.add_argument(
        "--growth_tradeoff",
        type=float,
        default=0.5,
        help="Tradeoff parameter for growth simulations.",
    )
    parser.add_argument(
        "--threads", type=int, default=2, help="Number of threads to use."
    )
    parser.add_argument(
        "--out_exchanges",
        type=str,
        default="results/micom/exchanges.tsv",
        help="Path to the output TSV file.",
    )
    return parser.parse_args()


def load_cgem_model(model_folder: str, model_file: str):
    cgem_path = f"{model_folder}/{model_file}"
    cgem = load_pickle(cgem_path)
    return cgem


def prepare_medium(medium_file: str, cgem):
    medium = pd.read_csv(medium_file, sep="\t", header=None)
    medium.columns = ["reaction", "flux"]
    medium = medium[medium.reaction.isin([r.id for r in cgem.exchanges])]
    return medium


def run_growth_simulations(
    manifest_file: str,
    model_folder: str,
    medium_file: str,
    tradeoff: float,
    threads: int,
    output_file: str,
):
    manifest = pd.read_csv(manifest_file, sep=",")
    for _, row in manifest.iterrows():
        cgem = load_cgem_model(model_folder, row["file"])
        medium = prepare_medium(medium_file, cgem)
        res = grow(
            manifest,
            model_folder=model_folder,
            medium=medium,
            tradeoff=tradeoff,
            threads=threads,
        )
        res.exchanges[res.exchanges.taxon != "medium"].to_csv(output_file, sep="\t")
    return res


def main():
    args = parse_arguments()
    result = run_growth_simulations(
        args.manifest,
        args.outdir,
        args.media_file,
        args.growth_tradeoff,
        args.threads,
        args.out_exchanges,
    )
    print("Growth simulations completed.")


if __name__ == "__main__":
    main()
