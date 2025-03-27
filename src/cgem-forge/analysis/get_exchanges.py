import argparse
import pandas as pd
from grow_workflow import grow
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
    parser.add_argument(
        "--atol",
        type=float,
        default=1e-6,
        help="Absolute tolerance for the solver.",
    )
    parser.add_argument(
        "--rtol",
        type=float,
        default=None,
        help="Relative tolerance for the solver.",
    )
    parser.add_argument(
        "--strategy",
        type=str,
        default="minimal imports",
        help="Strategy for setting exchange reactions.",
    )
    parser.add_argument(
        "--presolve",
        action="store_true",
        help="Whether to presolve the model before optimization.",
    )
    parser.add_argument(
        "--min_growth_cutoff",
        type=float,
        default=None,
        help="Minimal growth requirement for individual taxa. Set to 0 or leave unset for unconstrained growth.",
    )
    parser.add_argument(
        "--growth_pattern",
        type=str,
        default="growth",
        help="Pattern to identify growth reactions (default: 'growth'). Use 'biomass' or other patterns if your models use different naming conventions.",
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
    atol=1e-6,
    rtol=None,
    strategy="minimal imports",
    presolve=False,
    min_growth_cutoff=None,
    growth_pattern="growth",
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
            atol=atol,
            rtol=rtol,
            strategy=strategy,
            presolve=presolve,
            min_growth_cutoff=min_growth_cutoff,
            growth_pattern=growth_pattern,
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
        args.atol,
        args.rtol,
        args.strategy,
        args.presolve,
        args.min_growth_cutoff,
        args.growth_pattern,
    )
    print("Growth simulations completed.")
    
    # Print information about growth constraints if they were used
    if args.min_growth_cutoff is not None and args.min_growth_cutoff > 0:
        print(f"Individual taxa were constrained to grow at a minimum rate of {args.min_growth_cutoff}")
        print(f"Growth reactions were identified using the pattern '{args.growth_pattern}'")


if __name__ == "__main__":
    main()