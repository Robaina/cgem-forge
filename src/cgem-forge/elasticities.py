from __future__ import annotations
import numpy as np
import pandas as pd
from cobra.core import Model, Reaction
from cobra.flux_analysis import flux_variability_analysis
from rich.progress import track


STEP = 0.1


def split_fva_results(fva_results: pd.DataFrame) -> pd.Series:
    """
    Creates a pandas Series with forward and reverse fluxes for each reaction.

    Parameters:
    fva_results (pd.DataFrame): DataFrame containing FVA results with 'maximum' and 'minimum' columns.

    Returns:
    pd.Series: Series with reaction IDs (appended with "_forward" or "_reverse") as index and fluxes as values.
    """
    flux_dict = {
        f"{reaction_id}_forward": max_flux
        for reaction_id, max_flux in fva_results["maximum"].items()
    }
    flux_dict.update(
        {
            f"{reaction_id}_reverse": -min_flux
            for reaction_id, min_flux in fva_results["minimum"].items()
        }
    )
    return pd.Series(flux_dict)


def _elasticities_fva(before_fluxes: pd.Series, after_fluxes: pd.Series) -> pd.Series:
    """
    Calculate the derivatives using preprocessed FVA results for each reaction direction.

    Parameters:
    before_fluxes (pd.Series): Series of fluxes before perturbation.
    after_fluxes (pd.Series): Series of fluxes after perturbation.

    Returns:
    pd.Series: Series of calculated derivatives for each reaction.
    """
    eps = np.finfo(float).eps
    elasts = {
        reaction_id: (np.log1p(after_flux) - np.log1p(before_flux)) / STEP
        for reaction_id, before_flux, after_flux in zip(
            before_fluxes.index, before_fluxes, after_fluxes
        )
        if (before_flux > eps or after_flux > eps)
    }
    return pd.Series(elasts)


def elasticities_by_abundance_fva(
    com: Model,
    reactions: list[Reaction],
    fraction: float,
    progress: bool,
    processes: int = 2,
) -> pd.DataFrame:
    """
    Calculate the elasticities by running FVA before and after a perturbation in a community model.

    Parameters:
    com (Model): The community model.
    reactions (List[Reaction]): List of reactions to consider for FVA.
    fraction (float): Fraction of optimum for FVA calculation.
    progress (bool): Whether to display progress.

    Returns:
    pd.DataFrame: DataFrame containing elasticity results for reactions.
    """
    fva_before = flux_variability_analysis(
        com, reaction_list=reactions, fraction_of_optimum=fraction, processes=processes
    )
    fluxes_before = split_fva_results(fva_before)

    dfs = []
    abundance = com.abundances.copy()
    taxa = abundance.index

    if progress:
        taxa = track(taxa, description="Taxa")

    for taxon in taxa:
        original_abundance = abundance[taxon]
        abundance.loc[taxon] *= np.exp(STEP)
        com.set_abundance(abundance, normalize=False)
        fva_after = flux_variability_analysis(
            com, reaction_list=reactions, fraction_of_optimum=fraction, processes=1
        )
        fluxes_after = split_fva_results(fva_after)
        abundance.loc[taxon] = original_abundance
        com.set_abundance(abundance, normalize=False)

        elasts = _elasticities_fva(fluxes_before, fluxes_after)

        evaluated_reactions = [reaction_id for reaction_id in elasts.index]
        direction = [
            "forward" if "_forward" in reaction_id else "reverse"
            for reaction_id in elasts.index
        ]
        res = pd.DataFrame(
            {
                "reaction": evaluated_reactions,
                "taxon": taxon,
                "effector": taxon,
                "direction": direction,
                "elasticity": elasts.values,
            }
        )
        dfs.append(res)

    return pd.concat(dfs)
