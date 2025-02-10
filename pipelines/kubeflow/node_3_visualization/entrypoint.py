import argparse
from pathlib import Path
import matplotlib.pyplot as plt
from plot_interactions import (
    generate_bipartite_graph,
    plot_trophic_interactions,
    plot_exchange_heatmap,
    plot_metabolic_sankey,
    DEFAULT_HIDDEN_METABOLITES,
)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate cGEM visualization from MICOM exchanges"
    )

    # Input/Output
    parser.add_argument(
        "--exchanges-file",
        type=str,
        required=True,
        help="Path to the TSV file containing MICOM exchanges",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="results",
        help="Directory to store output files",
    )
    parser.add_argument(
        "--graph-output",
        type=str,
        default="bipartite_graph.json",
        help="Name of the output graph JSON file",
    )

    # Bipartite graph parameters
    parser.add_argument(
        "--hide-taxa",
        nargs="*",
        default=[],
        help="List of taxa to hide in the visualization",
    )
    parser.add_argument(
        "--hide-metabolites",
        nargs="*",
        default=[],
        help="Additional metabolites to hide in the visualization",
    )
    parser.add_argument(
        "--show-inorganic-compounds",
        action="store_true",
        help="Show common inorganic compounds that are hidden by default",
    )
    parser.add_argument(
        "--keep-metabolites",
        nargs="*",
        default=[],
        help="List of metabolites to specifically keep, even if they would be hidden by default",
    )
    parser.add_argument(
        "--flux-cutoff",
        type=str,
        default=None,
        help="Filter interactions by flux. Can be a number (minimum flux), 'top20' (top 20%%), or 'top10' (top 10%%) of interactions",
    )

    # Optional network parameters
    parser.add_argument(
        "--target-taxon",
        type=str,
        default=None,
        help="Target taxon to highlight (optional)",
    )
    parser.add_argument(
        "--medium-sources",
        nargs="*",
        default=None,
        help="List of environmental carbon sources (optional)",
    )
    parser.add_argument(
        "--target-compound",
        type=str,
        default=None,
        help="Target compound to focus on (optional)",
    )

    # Visualization parameters
    parser.add_argument(
        "--highlight-compounds",
        nargs="*",
        default=[],
        help="List of compounds to highlight",
    )
    parser.add_argument(
        "--highlight-color",
        type=str,
        default="violet",
        help="Color for highlighted nodes and edges",
    )
    parser.add_argument(
        "--edge-color",
        type=str,
        default="#7c7c7c",
        help="Color for non-highlighted edges",
    )
    parser.add_argument(
        "--node-color",
        type=str,
        default="silver",
        help="Color for non-highlighted nodes",
    )
    parser.add_argument(
        "--large-node-size", type=int, default=4000, help="Size of large nodes"
    )
    parser.add_argument(
        "--small-node-size", type=int, default=600, help="Size of small nodes"
    )
    parser.add_argument(
        "--edge-width-target",
        type=float,
        default=3.0,
        help="Edge width for target taxon",
    )
    parser.add_argument(
        "--edge-width-other",
        type=float,
        default=1.0,
        help="Edge width for other taxa",
    )
    parser.add_argument(
        "--arrow-size-target",
        type=int,
        default=10,
        help="Arrow size for target taxon",
    )
    parser.add_argument(
        "--arrow-size-other",
        type=int,
        default=15,
        help="Arrow size for other taxa",
    )
    parser.add_argument("--font-size", type=int, default=6, help="Font size for labels")
    parser.add_argument("--seed", type=int, default=2, help="Random seed for layout")

    # Additional visualization options
    parser.add_argument(
        "--visualization-type",
        type=str,
        choices=["network", "heatmap", "sankey"],
        default="network",
        help="Type of visualization to generate",
    )

    # Heatmap specific options
    parser.add_argument(
        "--normalize-heatmap", action="store_true", help="Normalize values in heatmap"
    )
    parser.add_argument(
        "--cluster-heatmap", action="store_true", help="Apply clustering to heatmap"
    )

    # Sankey specific options
    parser.add_argument(
        "--sankey-flux-cutoff",
        type=float,
        default=0.1,
        help="Minimum flux value to include in Sankey diagram",
    )

    return parser.parse_args()


def main():
    args = parse_args()

    # Create output directory if it doesn't exist
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Handle hidden metabolites
    hidden_metabolites = args.hide_metabolites.copy()
    if not args.show_inorganic_compounds:
        hidden_metabolites.extend(
            [m for m in DEFAULT_HIDDEN_METABOLITES if m not in args.keep_metabolites]
        )

    if args.visualization_type == "network":
        # Process flux_cutoff argument
        flux_cutoff = args.flux_cutoff
        if flux_cutoff is not None and flux_cutoff not in ["top20", "top10"]:
            try:
                flux_cutoff = float(flux_cutoff)
            except ValueError:
                raise ValueError("flux_cutoff must be a number, 'top20', or 'top10'")

        # Generate bipartite graph
        graph_output = output_dir / args.graph_output
        bipartite_graph = generate_bipartite_graph(
            args.exchanges_file,
            hide_taxa=args.hide_taxa,
            hide_metabolites=hidden_metabolites,
            keep_metabolites=args.keep_metabolites,
            flux_cutoff=flux_cutoff,
            target_taxon=args.target_taxon,
            environmental_carbon_sources=args.medium_sources,
            output_graph=str(graph_output),
        )

        # Create visualization
        fig, ax = plot_trophic_interactions(
            bipartite_graph=bipartite_graph,
            environmental_carbon_sources=args.medium_sources,
            figsize=(12, 12),
            highlight_compounds=args.highlight_compounds,
            target_taxon=args.target_taxon,
            target_compound=args.target_compound,
            highlight_color=args.highlight_color,
            edge_color=args.edge_color,
            node_color=args.node_color,
            large_node_size=args.large_node_size,
            small_node_size=args.small_node_size,
            edge_width_target_taxon=args.edge_width_target,
            edge_width_other=args.edge_width_other,
            arrow_size_target_taxon=args.arrow_size_target,
            arrow_size_other=args.arrow_size_other,
            font_size=args.font_size,
            seed=args.seed,
        )
        plt.savefig(
            output_dir / "trophic_interactions.png", dpi=300, bbox_inches="tight"
        )
        plt.close(fig)

    elif args.visualization_type == "heatmap":
        fig, ax = plot_exchange_heatmap(
            args.exchanges_file,
            normalize=args.normalize_heatmap,
            cluster=args.cluster_heatmap,
            output_path=str(output_dir / "exchange_heatmap.png"),
            hide_metabolites=hidden_metabolites,
            show_inorganic_compounds=args.show_inorganic_compounds,
        )
        plt.close(fig)

    elif args.visualization_type == "sankey":
        fig = plot_metabolic_sankey(
            args.exchanges_file,
            flux_cutoff=args.sankey_flux_cutoff,
            output_html=str(output_dir / "metabolic_sankey.html"),
            output_png=str(output_dir / "metabolic_sankey.png"),
            hide_metabolites=hidden_metabolites,
            show_inorganic_compounds=args.show_inorganic_compounds,
        )


if __name__ == "__main__":
    main()
