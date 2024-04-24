import argparse
import csv
from pathlib import Path
from typing import Dict, List, Tuple


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a TSV table from given arguments."
    )
    parser.add_argument("--sample_id", type=str, help="Sample ID")
    parser.add_argument("--abundances", type=str, help="Path to the abundance TSV file")
    parser.add_argument(
        "--gems_dir",
        type=str,
        help="Path to the directory where GEM files are stored",
    )
    parser.add_argument(
        "--out_taxatable",
        type=str,
        help="Path to the output TSV file",
        default="output.tsv",
    )
    parser.add_argument(
        "--base_path", help="Base directory path for external file system", default=""
    )
    return parser.parse_args()


def read_abundance_file(abundance_file: str) -> Dict[str, Tuple[str, str]]:
    with open(abundance_file, "r") as file:
        reader = csv.DictReader(file, delimiter="\t")
        return {row["id"]: (row["abundance"], row["taxonomy"]) for row in reader}


def get_ids_and_extensions_from_gem_directory(
    gem_directory: str,
) -> List[Tuple[str, str]]:
    id_extensions = []
    directory = Path(gem_directory)
    for file_path in directory.glob("*"):
        if file_path.suffix in [".xml", ".json"]:
            id_extensions.append((file_path.stem, file_path.suffix))
    return id_extensions


def build_output_table(
    sample_id: str,
    abundance_data: Dict[str, Tuple[str, str]],
    gem_directory: str,
    id_extensions: List[Tuple[str, str]],
    base_path: str = "",
) -> List[List[str]]:
    output_data = []
    for id, extension in id_extensions:
        abundance, taxonomy = abundance_data.get(id, ("0", "Unknown"))
        original_file_path = Path(gem_directory) / f"{id}{extension}"
        if base_path:
            file_path = Path(base_path) / f"{id}{extension}"
        else:
            file_path = original_file_path
        output_data.append([sample_id, id, abundance, taxonomy, str(file_path)])
    return output_data


def write_output_table(output_data: List[List[str]], output_file: str) -> None:
    with open(output_file, "w", newline="") as file:
        writer = csv.writer(file, delimiter="\t")
        writer.writerow(["sample_id", "id", "abundance", "taxonomy", "file"])
        writer.writerows(output_data)


def main() -> None:
    args = parse_arguments()
    abundance_data = read_abundance_file(args.abundances)
    id_extensions = get_ids_and_extensions_from_gem_directory(args.gems_dir)
    output_data = build_output_table(
        args.sample_id,
        abundance_data,
        args.gems_dir,
        id_extensions,
        args.base_path,
    )
    write_output_table(output_data, args.out_taxatable)


if __name__ == "__main__":
    main()
