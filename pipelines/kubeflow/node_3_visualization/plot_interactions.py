# plot_interactions.py
from __future__ import annotations
from pathlib import Path
import json
import random
import networkx as nx
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import seaborn as sns
import pandas as pd


DEFAULT_HIDDEN_METABOLITES = [
    "h",
    "h2",
    "btn",
    "ca2",
    "cl",
    "co2",
    "cu2",
    "fe2",
    "fe3",
    "k",
    "no2",
    "no3",
    "so4",
    "thm",
    "zn2",
    "pi",
    "h2o",
    "h2o2",
    "o2",
    "cobalt2",
    "nh4",
    "hco3",
    "mg2",
    "mn2",
]


def generate_bipartite_graph(
    exchanges_file_path: str,
    hide_taxa: list[str] = None,
    hide_metabolites: list[str] = None,
    flux_cutoff: float | str = None,
    target_taxon: str = None,
    environmental_carbon_sources: list[str] = None,
    output_graph: Path = None,
    relabel_nodes: dict = None,
    keep_metabolites: list[str] = None,
) -> nx.DiGraph:
    """
    Generates a bipartite graph from a file containing exchange data.

    Args:
        exchanges_file_path (str): The path to the file containing exchange data.
        hide_taxa (list[str], optional): A list of taxa to hide from the graph. Defaults to None.
        hide_metabolites (list[str], optional): A list of metabolites to hide from the graph. Defaults to None.
        flux_cutoff (float | str, optional): Can be:
            - a float number (minimum flux to include)
            - 'top20' (keep top 20% of interactions)
            - 'top10' (keep top 10% of interactions)
            Defaults to None.
        target_taxon (str, optional): The target taxon to focus on in the graph. Defaults to None.
        environmental_carbon_sources (list[str], optional): A list of environmental carbon sources. Defaults to None.
        output_graph (Path, optional): Path to save the JSON graph file. Defaults to None.
        relabel_nodes (dict, optional): Dictionary to relabel nodes. Defaults to None.
        keep_metabolites (list[str], optional): List of metabolites to keep regardless of connectivity. Defaults to None.

    Returns:
        nx.DiGraph: The generated bipartite graph.
    """
    G = nx.DiGraph()
    if relabel_nodes is not None:
        G = nx.relabel_nodes(G, relabel_nodes)

    # Store all fluxes and their corresponding information
    all_interactions = []
    with open(exchanges_file_path, "r") as f:
        for line in f:
            if "taxon" in line:
                continue
            cols = line.strip().split("\t")
            taxon = cols[1].replace("_sp", "")
            metabolite = cols[7].replace("_e", "")
            if relabel_nodes is not None and metabolite in relabel_nodes:
                metabolite = relabel_nodes[metabolite]
            direction = cols[8]
            flux = abs(float(cols[5]))

            # Store interaction info
            all_interactions.append(
                {
                    "taxon": taxon,
                    "metabolite": metabolite,
                    "direction": direction,
                    "flux": flux,
                }
            )

    # Sort interactions by flux magnitude
    all_interactions.sort(key=lambda x: x["flux"], reverse=True)

    # Handle flux cutoff
    if isinstance(flux_cutoff, str):
        if flux_cutoff == "top20":
            percentage = 0.2
        elif flux_cutoff == "top10":
            percentage = 0.1
        else:
            raise ValueError("flux_cutoff string must be either 'top20' or 'top10'")

        # Keep top percentage of interactions by flux magnitude
        cutoff_idx = max(1, int(len(all_interactions) * percentage))
        min_flux = all_interactions[cutoff_idx - 1]["flux"]
        all_interactions = [
            inter for inter in all_interactions if inter["flux"] >= min_flux
        ]
    elif flux_cutoff is not None:
        # Use numeric cutoff
        all_interactions = [
            inter for inter in all_interactions if inter["flux"] >= flux_cutoff
        ]

    # Process filtered interactions
    for interaction in all_interactions:
        taxon = interaction["taxon"]
        metabolite = interaction["metabolite"]
        direction = interaction["direction"]

        if hide_taxa is None or taxon not in hide_taxa:
            G.add_node(taxon, bipartite=0)
        if hide_metabolites is None or metabolite not in hide_metabolites:
            if (
                environmental_carbon_sources is None
                or metabolite in environmental_carbon_sources
            ):
                G.add_node(metabolite, bipartite=1)
            elif target_taxon is not None and (
                taxon == target_taxon or metabolite == target_taxon
            ):
                G.add_node(metabolite, bipartite=1)

        if direction == "export":
            G.add_edge(taxon, metabolite)
        elif direction == "import":
            G.add_edge(metabolite, taxon)

    if hide_taxa is not None:
        G.remove_nodes_from(hide_taxa)
    if hide_metabolites is not None:
        G.remove_nodes_from(hide_metabolites)

    for source in environmental_carbon_sources or []:
        if source not in G.nodes:
            G.add_node(source, bipartite=1)

    if target_taxon is not None:
        for node in list(G.nodes):
            if (
                "bipartite" in G.nodes[node]
                and (node not in (environmental_carbon_sources or []))
                and G.nodes[node]["bipartite"] == 1
            ):
                if not G.has_edge(node, target_taxon) and (
                    keep_metabolites is None or node not in keep_metabolites
                ):
                    G.remove_node(node)

    G.remove_nodes_from(list(nx.isolates(G)))

    if output_graph is not None:
        data = nx.readwrite.json_graph.node_link_data(G)
        with open(output_graph, "w") as f:
            json.dump(data, f)

    return G


def plot_trophic_interactions(
    bipartite_graph: nx.DiGraph,
    environmental_carbon_sources: list[str] = None,
    ax: plt.Axes = None,
    figsize: tuple = (10, 10),
    highlight_compounds: list[str] = None,
    target_taxon: str = None,
    target_compound: str = None,
    highlight_color: str = "violet",
    edge_color: str = "lightgrey",
    node_color: str = "silver",
    large_node_size: int = 6000,
    small_node_size: int = 1000,
    edge_width_target_taxon: float = 3.5,
    edge_width_other: float = 0.8,
    arrow_size_target_taxon: int = 10,
    arrow_size_other: int = 5,
    font_size: int = 8,
    seed: int = None,
) -> tuple[plt.Figure, plt.Axes]:
    """
    Plot trophic interactions from a bipartite graph.

    Args:
        bipartite_graph (nx.DiGraph): The bipartite graph to plot.
        environmental_carbon_sources (list[str], optional): List of environmental carbon sources. Defaults to None.
        ax (plt.Axes, optional): Matplotlib axes to plot on. If None, creates new figure.
        figsize (tuple, optional): Figure size if creating new figure. Defaults to (10, 10).
        highlight_compounds (list[str], optional): List of compounds to highlight. Defaults to None.
        target_taxon (str, optional): Target taxon to focus on. Defaults to None.
        target_compound (str, optional): Target compound to focus on. Defaults to None.
        highlight_color (str, optional): Color for highlighted nodes and edges. Defaults to "violet".
        edge_color (str, optional): Color for non-highlighted edges. Defaults to "lightgrey".
        node_color (str, optional): Color for non-highlighted nodes. Defaults to "silver".
        large_node_size (int, optional): Size for taxa nodes. Defaults to 6000.
        small_node_size (int, optional): Size for metabolite nodes. Defaults to 1000.
        edge_width_target_taxon (float, optional): Edge width for target taxon. Defaults to 3.5.
        edge_width_other (float, optional): Edge width for other taxa. Defaults to 0.8.
        arrow_size_target_taxon (int, optional): Arrow size for target taxon. Defaults to 10.
        arrow_size_other (int, optional): Arrow size for other taxa. Defaults to 5.
        font_size (int, optional): Font size for labels. Defaults to 8.
        seed (int, optional): Random seed for layout. Defaults to None.
    """
    if highlight_compounds is None:
        highlight_compounds = []
    if environmental_carbon_sources is None:
        environmental_carbon_sources = []

    if seed is None:
        seed = random.randint(0, 100)

    # Create figure and axes if not provided
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
        fig.set_facecolor("black")
    else:
        fig = ax.figure

    # Get nodes connected to highlighted compounds
    taxon_nodes_connected_to_highlight = []
    if highlight_compounds:
        taxon_nodes_connected_to_highlight = [
            n
            for compound in highlight_compounds
            for n in bipartite_graph.neighbors(compound)
            if bipartite_graph.nodes[n]["bipartite"] == 0
        ]

    # Get direct and indirect nodes
    direct_nodes = []
    indirect_nodes = []
    indirect_nodes_extended = []
    if target_compound is not None:
        direct_nodes = list(bipartite_graph.neighbors(target_compound)) + [
            target_compound
        ]
        indirect_nodes = [
            neighbor
            for node in direct_nodes
            for neighbor in bipartite_graph.neighbors(node)
        ]
        indirect_nodes_extended = [
            neighbor
            for node in indirect_nodes
            for neighbor in bipartite_graph.neighbors(node)
        ]

    # Get compounds connected to target taxon
    target_taxon_compounds = []
    species_connected_to_target_taxon_compounds = []
    if target_taxon is not None:
        target_taxon_compounds = [
            n
            for n in bipartite_graph.to_undirected().neighbors(target_taxon)
            if bipartite_graph.nodes[n]["bipartite"] == 1
        ]
        species_connected_to_target_taxon_compounds = [
            n
            for compound in target_taxon_compounds
            for n in bipartite_graph.neighbors(compound)
            if bipartite_graph.nodes[n]["bipartite"] == 0
        ]

    # Create subgraph
    subgraph_nodes = set(
        direct_nodes
        + indirect_nodes
        + indirect_nodes_extended
        + target_taxon_compounds
        + species_connected_to_target_taxon_compounds
        + highlight_compounds
    )

    # If no specific nodes are selected, use all nodes
    if not subgraph_nodes:
        subgraph_nodes = set(bipartite_graph.nodes())

    subgraph = bipartite_graph.subgraph(subgraph_nodes)

    # Add medium donor edges if medium sources are provided
    extended_subgraph = nx.DiGraph(subgraph)
    if environmental_carbon_sources:
        medium_donor_edges = [
            (u, v)
            for u, v in bipartite_graph.edges()
            if u in environmental_carbon_sources
            and bipartite_graph.nodes[v]["bipartite"] == 0
        ]
        extended_subgraph.add_edges_from(medium_donor_edges)

    # Set bipartite attribute for new nodes
    for node in extended_subgraph.nodes():
        if "bipartite" not in extended_subgraph.nodes[node]:
            extended_subgraph.nodes[node]["bipartite"] = 1

    # Create layout
    shell_layout = nx.shell_layout(
        extended_subgraph,
        [
            {n for n, d in extended_subgraph.nodes(data=True) if d["bipartite"] == 0},
            {n for n, d in extended_subgraph.nodes(data=True) if d["bipartite"] == 1},
        ],
        rotate=seed,
    )

    # Split graph into highlighted and non-highlighted parts
    non_highlight_edges = [
        (u, v)
        for u, v in extended_subgraph.edges()
        if u not in highlight_compounds and v not in highlight_compounds
    ]
    highlight_edges = [
        (u, v)
        for u, v in extended_subgraph.edges()
        if u in highlight_compounds or v in highlight_compounds
    ]

    non_highlight_subgraph = extended_subgraph.edge_subgraph(non_highlight_edges)
    highlight_subgraph = extended_subgraph.edge_subgraph(highlight_edges)

    # Draw non-highlighted part
    nx.draw(
        non_highlight_subgraph,
        shell_layout,
        with_labels=False,
        node_size=[
            large_node_size if d["bipartite"] == 0 else small_node_size
            for _, d in non_highlight_subgraph.nodes(data=True)
        ],
        node_color=[
            (
                highlight_color
                if (
                    node in highlight_compounds
                    or (target_taxon and node == target_taxon)
                    or node in taxon_nodes_connected_to_highlight
                )
                else node_color
            )
            for node in non_highlight_subgraph.nodes()
        ],
        edge_color=edge_color,
        arrowsize=arrow_size_other,
        width=edge_width_other,
        ax=ax,
    )

    # Draw highlighted part
    if highlight_edges:
        nx.draw(
            highlight_subgraph,
            shell_layout,
            with_labels=False,
            node_size=[
                large_node_size if d["bipartite"] == 0 else 2 * small_node_size
                for _, d in highlight_subgraph.nodes(data=True)
            ],
            node_color=[
                (
                    highlight_color
                    if (
                        node in highlight_compounds
                        or (target_taxon and node == target_taxon)
                        or node in taxon_nodes_connected_to_highlight
                    )
                    else node_color
                )
                for node in highlight_subgraph.nodes()
            ],
            edge_color=highlight_color,
            arrowsize=arrow_size_target_taxon,
            width=edge_width_target_taxon,
            ax=ax,
        )

    # Draw labels
    highlight_nodes = list(highlight_subgraph.nodes) if highlight_edges else []
    non_highlight_nodes = [
        node for node in extended_subgraph.nodes if node not in highlight_nodes
    ]

    nx.draw_networkx_labels(
        extended_subgraph,
        shell_layout,
        labels={n: n for n in non_highlight_nodes},
        font_size=font_size,
        ax=ax,
    )

    if highlight_nodes:
        nx.draw_networkx_labels(
            extended_subgraph,
            shell_layout,
            labels={n: n for n in highlight_nodes},
            font_size=1.5 * font_size,
            ax=ax,
        )

    ax.set_facecolor("black")
    ax.axis("off")

    return fig, ax


def plot_exchange_heatmap(
    exchanges_file_path: str,
    normalize: bool = True,
    cluster: bool = True,
    output_path: str = None,
    hide_metabolites: list[str] = None,
    show_inorganic_compounds: bool = False,
) -> tuple[plt.Figure, plt.Axes]:
    """
    Creates a heatmap visualization of metabolic exchanges.

    Args:
        exchanges_file_path: Path to the exchanges TSV file
        normalize: Whether to normalize flux values
        cluster: Whether to apply hierarchical clustering
        output_path: Path to save the plot
        hide_metabolites: List of metabolites to hide from visualization
        show_inorganic_compounds: Whether to show inorganic compounds

    Returns:
        Figure and Axes objects
    """
    # Read data
    exchanges = pd.read_csv(exchanges_file_path, sep="\t")

    # Handle metabolite filtering
    metabolites_to_hide = []
    if hide_metabolites is not None:
        metabolites_to_hide.extend(hide_metabolites)
    if not show_inorganic_compounds:
        metabolites_to_hide.extend(DEFAULT_HIDDEN_METABOLITES)

    # Filter out hidden metabolites
    if metabolites_to_hide:
        exchanges = exchanges[
            ~exchanges["metabolite"].str.replace("_e", "").isin(metabolites_to_hide)
        ]

    # Pivot data for heatmap
    matrix = exchanges.pivot_table(
        values="flux", index="taxon", columns="metabolite", aggfunc="sum", fill_value=0
    )

    if normalize:
        matrix = (matrix - matrix.mean()) / matrix.std()

    # Create plot
    if cluster:
        g = sns.clustermap(
            matrix,
            cmap="RdBu_r",
            center=0,
            figsize=(12, 8),
            dendrogram_ratio=(0.1, 0.2),
            cbar_pos=(0.02, 0.32, 0.03, 0.2),
        )
        fig = g.fig
        ax = g.ax_heatmap
    else:
        fig, ax = plt.subplots(figsize=(12, 8))
        sns.heatmap(matrix, cmap="RdBu_r", center=0, ax=ax)

    plt.title("Metabolic Exchange Patterns")

    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches="tight")

    return fig, ax


def plot_metabolic_sankey(
    exchanges_file_path: str,
    flux_cutoff: float = 0.1,
    output_html: str = None,
    output_png: str = None,
    hide_metabolites: list[str] = None,
    show_inorganic_compounds: bool = False,
) -> go.Figure:
    """
    Creates a Sankey diagram showing metabolic fluxes between taxa and compounds.

    Args:
        exchanges_file_path: Path to the exchanges TSV file
        flux_cutoff: Minimum flux value to include
        output_html: Path to save interactive HTML plot
        output_png: Path to save static PNG plot
        hide_metabolites: List of metabolites to hide from visualization
        show_inorganic_compounds: Whether to show inorganic compounds

    Returns:
        Plotly figure object
    """
    # Read exchanges data
    exchanges = pd.read_csv(exchanges_file_path, sep="\t")

    # Handle metabolite filtering
    metabolites_to_hide = []
    if hide_metabolites is not None:
        metabolites_to_hide.extend(hide_metabolites)
    if not show_inorganic_compounds:
        metabolites_to_hide.extend(DEFAULT_HIDDEN_METABOLITES)

    # Filter out hidden metabolites
    if metabolites_to_hide:
        exchanges = exchanges[
            ~exchanges["metabolite"].str.replace("_e", "").isin(metabolites_to_hide)
        ]

    # Process nodes and links
    taxa = exchanges["taxon"].unique()
    metabolites = exchanges["metabolite"].unique()

    # Create node lists with original colors
    node_labels = list(taxa) + list(metabolites)
    node_colors = ["#1f77b4"] * len(taxa) + ["#2ca02c"] * len(
        metabolites
    )  # Blue for taxa, green for metabolites

    # Create links
    links = []
    for _, row in exchanges.iterrows():
        if abs(row["flux"]) >= flux_cutoff:
            if row["direction"] == "export":
                source = list(taxa).index(row["taxon"])
                target = len(taxa) + list(metabolites).index(row["metabolite"])
            else:
                source = len(taxa) + list(metabolites).index(row["metabolite"])
                target = list(taxa).index(row["taxon"])
            links.append(
                {
                    "source": source,
                    "target": target,
                    "value": abs(row["flux"]),
                    "color": "rgba(127, 127, 127, 0.4)",  # Translucent grey for links
                }
            )

    # Common Sankey settings to ensure consistent appearance
    sankey_data = go.Sankey(
        node=dict(
            pad=15,  # Node padding
            thickness=20,  # Node thickness
            line=dict(color="black", width=0.5),
            label=node_labels,
            color=node_colors,
        ),
        link=dict(
            source=[link["source"] for link in links],
            target=[link["target"] for link in links],
            value=[link["value"] for link in links],
            color=[link["color"] for link in links],
        ),
    )

    # Common layout settings
    common_layout = dict(
        title_text="Metabolic Flux Distribution",
        font_size=12,
        autosize=True,  # Allow diagram to be responsive
        margin=dict(l=25, r=25, t=25, b=25),  # Compact margins
    )

    # Create interactive HTML figure with transparent background
    fig = go.Figure(data=[sankey_data])
    fig.update_layout(
        **common_layout, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)"
    )

    # Save interactive HTML
    if output_html:
        fig.write_html(output_html)

    # Create and save static PNG figure with white background
    if output_png:
        fig_static = go.Figure(data=[sankey_data])
        fig_static.update_layout(
            **common_layout,
            width=1200,
            height=800,
            paper_bgcolor="white",
            plot_bgcolor="white",
        )
        fig_static.write_image(output_png)

    return fig
