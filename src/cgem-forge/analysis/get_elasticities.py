import argparse
from micom.elasticity import elasticities
from micom import load_pickle


def parse_arguments():
    parser = argparse.ArgumentParser(description="Calculate elasticities using MICOM.")
    parser.add_argument(
        "--cgem_pickle", type=str, help="Path to the CGEM model file (Pickle format)."
    )
    parser.add_argument(
        "--growth_tradeoff",
        type=float,
        default=0.5,
        help="Growth tradeoff parameter for elasticity calculation.",
    )
    parser.add_argument(
        "--out_elasticities",
        type=str,
        default="results/micom/elasticities.tsv",
        help="Path to the output TSV file.",
    )
    return parser.parse_args()


def calculate_elasticities(cgem_file: str, fraction: float, output_file: str):
    cgem = load_pickle(cgem_file)
    eps = elasticities(cgem, fraction=fraction, reactions=cgem.exchanges)
    eps.to_csv(output_file, sep="\t", index=False)
    return eps


def main():
    args = parse_arguments()
    eps = calculate_elasticities(
        args.cgem_pickle, args.growth_tradeoff, args.out_elasticities
    )
    print("Elasticity calculations completed.")


if __name__ == "__main__":
    main()
