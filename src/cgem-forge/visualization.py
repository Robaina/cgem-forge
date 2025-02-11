import json
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
from pandas import DataFrame, Series

import networkx as nx
from networkx.readwrite import json_graph


def plot_flux_distribution(
    sample: DataFrame,
    reaction_ids: list,
    histogram: bool = False,
    fva: DataFrame = None,
    figsize_per_plot: tuple = (4, 3),
    n_colums: int = 3,
):
    """Plot the flux ranges and sample for a list of reactions.

    Args:
        sample (DataFrame): DataFrame with sampled flux distributions.
        reaction_ids (list): List of reaction IDs to plot.
        histogram (bool, optional): Whether to overlay a histogram. Defaults to False.
        fva (DataFrame, optional): DataFrame with flux variability analysis results. Defaults to None.
        figsize_per_plot (tuple, optional): Size of each individual plot. Defaults to (10, 6).
    """

    n_reactions = len(reaction_ids)
    n_rows = (n_reactions + 1) // n_colums

    fig, axes = plt.subplots(
        n_rows,
        n_colums,
        figsize=(figsize_per_plot[0] * n_colums, figsize_per_plot[1] * n_rows),
    )
    if n_reactions == 1:
        axes = [[axes]]
    elif n_reactions % n_colums != 0:
        for j in range(n_colums - 1, n_reactions % n_colums - 1, -1):
            fig.delaxes(axes[-1, j])

    handles, labels = [], []
    for i, reaction_id in enumerate(reaction_ids):
        ax = axes[i // n_colums, i % n_colums]

        if histogram:
            sns.histplot(
                sample[reaction_id],
                kde=True,
                bins=30,
                color="skyblue",
                label="Histogram",
                ax=ax,
            )
        sns.kdeplot(
            sample[reaction_id],
            color="blue",
            label="Density Estimation",
            fill=True,
            ax=ax,
        )

        if fva is not None:
            min_flux = fva.loc[reaction_id, "minimum"]
            max_flux = fva.loc[reaction_id, "maximum"]
            line1 = ax.axvline(min_flux, color="r", linestyle="--")
            line2 = ax.axvline(max_flux, color="b", linestyle="--")

        ax.set_title(f"{reaction_id}")
        ax.set_xlabel("mmol/gDW/h")
        ax.set_ylabel("Density")

    handles, labels = axes[0, 0].get_legend_handles_labels()
    if fva is not None:
        handles += [line1, line2]
        labels += [f"Min Flux: {min_flux:.2f}", f"Max Flux: {max_flux:.2f}"]

    fig.legend(handles, labels, loc="lower right", bbox_to_anchor=(0.95, 0.05))
    plt.tight_layout()
    plt.show()


def rename_rxn_ids_for_escher(fluxes: Series, reaction_mapping: dict):
    """
    Rename reaction IDs to be compatible with E. coli escher map.

    Args:
    - fluxes (pd.Series): Input fluxes.
    - mapping (dict): Dictionary containing a subset of the entries
                      as keys and the new IDs as values.

    Returns:
    - pd.Series: Series with renamed reaction IDs.
    """
    base_ids = fluxes.index.str.extract(r"(.+?)_(?:c|h|m|x)")[0].dropna().astype(str)
    unique_reactions = base_ids[~base_ids.duplicated(keep=False)].unique()
    duplicated_reactions = base_ids[base_ids.duplicated(keep=False)].unique()
    c_reactions = [r for r in duplicated_reactions if r + "_c" in fluxes.index]
    m_reactions = [
        r
        for r in duplicated_reactions
        if r + "_m" in fluxes.index and r not in c_reactions
    ]

    # If in ore than one compartment, keep "c", then "m", then any other.
    def custom_replace(s):
        base, comp = s.rsplit("_", 1)
        if base in unique_reactions:
            return base
        elif base in c_reactions and comp == "c":
            return base
        elif base in m_reactions and comp == "m":
            return base
        elif (
            base in duplicated_reactions
            and base not in c_reactions
            and base not in m_reactions
        ):
            return base
        else:
            return s

    fluxes.index = fluxes.index.map(custom_replace)
    fluxes = fluxes.groupby(fluxes.index).first().rename(index=reaction_mapping)
    return fluxes


def get_graph_object_from_smetana_table(
    smetana_table: DataFrame, weight: str = None, output_graph: Path = None
) -> nx.DiGraph:
    """Create a bipartite graph object from a smetana table.

    Args:
        smetana_table (DataFrame): _description_
        output_graph (Path, optional): _description_. Defaults to None.

    Returns:
        nx.DiGraph: _description_
    """
    B = nx.DiGraph()
    for i, row in smetana_table.iterrows():
        if weight is not None:
            edge_weight = row[weight]
        else:
            edge_weight = ""
        donor_id = row["donor"]
        receiver_id = row["receiver"]
        compound_id = row["compound"]
        B.add_edge(donor_id, compound_id, weight=edge_weight)
        B.add_edge(compound_id, receiver_id, weight=edge_weight)
        B.add_node(donor_id, bipartite=0, group="genome")
        B.add_node(receiver_id, bipartite=0, group="genome")
        B.add_node(compound_id, bipartite=1, group="compound")
    if output_graph is not None:
        graph_data = json_graph.cytoscape_data(B)
        json.dump(graph_data, open(output_graph, "w"))
    return B
