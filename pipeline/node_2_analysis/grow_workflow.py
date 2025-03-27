"""Performs growth and exchange analysis for several models with individual growth constraints."""

from cobra.util.solver import interface_to_str, OptimizationError
from micom import load_pickle
from micom.annotation import annotate_metabolites_from_exchanges
from micom.logger import logger
from micom.media import minimal_medium
from micom.workflows.core import workflow
from micom.workflows.results import GrowthResults
from micom.workflows.media import process_medium
from os import path
import pandas as pd
import warnings
from cgem_utils import set_minimal_growth_requirements, reset_growth_requirements

warnings.filterwarnings("ignore", category=pd.errors.PerformanceWarning)


DIRECTION = pd.Series(["import", "export"], index=[0, 1])


ARGS = {
    "none": {"fluxes": True, "pfba": False},
    "minimal imports": {"fluxes": False, "pfba": False},
    "pFBA": {"fluxes": True, "pfba": True},
}


def _growth(args):
    p, tradeoff, medium, weights, strategy, atol, rtol, presolve, min_growth_cutoff, growth_pattern = args
    com = load_pickle(p)

    if atol is None:
        atol = com.solver.configuration.tolerances.feasibility
    if rtol is None:
        rtol = com.solver.configuration.tolerances.feasibility
    if presolve:
        # looks stupid but that here is to respect the preset
        # and there is an auto setting that we want to respect
        com.solver.configuration.presolve = presolve

    if "glpk" in interface_to_str(com.solver.interface):
        logger.error(
            "Community models were not built with a QP-capable solver. "
            "This means that you did not install CPLEX or Gurobi. "
            "If you did install one of the two please file a bug report "
            "at https://github.com/micom-dev/micom/issues."
        )
        return None

    ex_ids = [r.id for r in com.exchanges]
    logger.info(
        "%d/%d import reactions found in model.",
        medium.index.isin(ex_ids).sum(),
        len(medium),
    )
    com.medium = medium[medium.index.isin(ex_ids)]

    # Set minimal growth requirements if requested
    if min_growth_cutoff is not None and min_growth_cutoff > 0:
        logger.info(
            "Setting minimal growth requirements (cutoff: %g) for individual taxa in %s",
            min_growth_cutoff, com.id
        )
        try:
            set_minimal_growth_requirements(com, min_growth_cutoff, growth_pattern=growth_pattern)
        except ValueError as e:
            logger.warning(
                "Could not set minimal growth requirements for %s: %s",
                com.id, str(e)
            )

    # Get growth rates
    args = ARGS[strategy].copy()
    args["atol"] = atol
    args["rtol"] = rtol
    args["fraction"] = tradeoff
    try:
        sol = com.cooperative_tradeoff(**args)
        rates = sol.members
        rates["taxon"] = rates.index
        rates["tradeoff"] = tradeoff
        rates["sample_id"] = com.id
    except Exception as e:
        logger.error(
            "Could not solve cooperative tradeoff for %s: %s. "
            "This can often be fixed by enabling `presolve`, choosing more "
            "permissive atol and rtol arguments, or by checking that medium "
            "fluxes are > atol." % (com.id, str(e))
        )
        # Reset growth requirements if they were set
        if min_growth_cutoff is not None and min_growth_cutoff > 0:
            try:
                reset_growth_requirements(com, growth_pattern=growth_pattern)
            except Exception:
                pass
        return None

    if strategy == "minimal imports":
        # Get the minimal medium and the solution at the same time
        med = minimal_medium(
            com,
            exchanges=None,
            community_growth=sol.growth_rate,
            min_growth=rates.growth_rate.drop("medium"),
            solution=True,
            weights=weights,
            atol=atol,
            rtol=rtol,
        )
        if med is None:
            logger.error(
                "The minimal medium optimization failed for %s. "
                "This can often be fixed by enabling `presolve`, choosing more "
                "permissive atol and rtol arguments, or by checking that medium "
                "fluxes are > atol." % com.id
            )
            # Reset growth requirements if they were set
            if min_growth_cutoff is not None and min_growth_cutoff > 0:
                try:
                    reset_growth_requirements(com, growth_pattern=growth_pattern)
                except Exception:
                    pass
            return None
        sol = med["solution"]

    # Reset growth requirements if they were set
    if min_growth_cutoff is not None and min_growth_cutoff > 0:
        try:
            reset_growth_requirements(com, growth_pattern=growth_pattern)
        except Exception:
            pass

    exs = list({r.global_id for r in com.internal_exchanges + com.exchanges})
    fluxes = sol.fluxes.loc[:, exs].copy()
    fluxes["sample_id"] = com.id
    fluxes["tolerance"] = atol
    anns = annotate_metabolites_from_exchanges(com)
    return {"growth": rates, "exchanges": fluxes, "annotations": anns}


def grow(
    manifest,
    model_folder,
    medium,
    tradeoff,
    threads=1,
    weights=None,
    strategy="minimal imports",
    atol=None,
    rtol=None,
    presolve=False,
    min_growth_cutoff=None,
    growth_pattern="growth",
):
    """Simulate growth for a set of community models.

    Note
    ----
    The strategy `mimimal imports` can become unstable for common carbon sources since
    it will add in infeasible imports that are very small but import some high-C
    molecules. If you use it check that only components from your medium have been used
    and molecules that should be essential are indeed consumed.

    Parameters
    ----------
    manifest : pandas.DataFrame
        The manifest as returned by the `build` workflow.
    model_folder : str
        The folder in which to find the files mentioned in the manifest.
    medium : pandas.DataFrame
        A growth medium. Must have columns "reaction" and "flux" denoting
        exchange reactions and their respective maximum flux.
    tradeoff : float in (0.0, 1.0]
        A tradeoff value. Can be chosen by running the `tradeoff` workflow or
        by experince. Tradeoff values of 0.5 for metagenomcis data and 0.3 for
        16S data seem to work well.
    threads : int >=1
        The number of parallel workers to use when building models. As a
        rule of thumb you will need around 1GB of RAM for each thread.
    strategy : str
        Computational strategy used to reduce the flux space. Default "minimal imports"
        uses the solution with the smallest total import flux from the environment,
        "pFBA" uses parsimonious FBA, and "none" returns an arbitrary
        feasible flux distribution.
    weights : str
        Only used during the calculaton of the minimal import rates.
        Will scale the fluxes by a weight factor. Can either be "mass" which will
        scale by molecular mass, a single element which will scale by
        the elemental content (for instance "C" to scale by carbon content).
        If None every metabolite will receive the same weight.
        Will be ignored if `minimize_components` is True.
    atol : float
        Absolute tolerance for the growth rates. If None will use the solver tolerance.
    rtol : float
        Relative tolerqance for the growth rates. If None will use the solver tolerance.
    presolve : bool
        Whether to use the presolver/scaling. Can improve numerical accuracy in some
        cases.
    min_growth_cutoff : float, optional
        If provided, sets a minimal growth requirement for all individual taxa.
        Must be a positive float or None. If None, no growth constraints will be applied.
    growth_pattern : str, default "growth"
        Pattern to search for in reaction IDs to identify growth reactions.
        Only used if min_growth_cutoff is not None.

    Returns
    -------
    GrowthResults
        A named tuple containing the growth rates and exchange fluxes for all
        samples/models.
    """
    if strategy not in ARGS:
        raise ValueError(
            "`%s` is not a valid strategy. Must be one of %s!"
            % (strategy, ", ".join(ARGS))
        )
    
    if min_growth_cutoff is not None and min_growth_cutoff < 0:
        raise ValueError(
            "min_growth_cutoff must be a positive float or None. "
            "Got %g instead." % min_growth_cutoff
        )
        
    samples = manifest.sample_id.unique()
    paths = {
        s: path.join(model_folder, manifest[manifest.sample_id == s].file.iloc[0])
        for s in samples
    }
    medium = process_medium(medium, samples)
    args = [
        [
            p,
            tradeoff,
            medium.flux[medium.sample_id == s],
            weights,
            strategy,
            atol,
            rtol,
            presolve,
            min_growth_cutoff,
            growth_pattern,
        ]
        for s, p in paths.items()
    ]
    results = workflow(_growth, args, threads)
    if all([r is None for r in results]):
        raise OptimizationError(
            "All numerical optimizations failed. This indicates a problem "
            "with the solver or numerical instabilities. Check that you have "
            "CPLEX or Gurobi installed. You may also increase the abundance "
            "cutoff to create simpler models."
        )
    growth = pd.concat(r["growth"] for r in results if r is not None)
    growth = growth[growth.taxon != "medium"]
    exchanges = pd.concat(r["exchanges"] for r in results if r is not None)
    exchanges["taxon"] = exchanges.index.values
    exchanges = exchanges.melt(
        id_vars=["taxon", "sample_id", "tolerance"],
        var_name="reaction",
        value_name="flux",
    ).dropna(subset=["flux"])
    abundance = growth[["taxon", "sample_id", "abundance"]]
    exchanges = pd.merge(exchanges, abundance, on=["taxon", "sample_id"], how="outer")
    anns = pd.concat(
        r["annotations"] for r in results if r is not None
    ).drop_duplicates(subset=["reaction"])
    anns.index = anns.reaction
    exchanges = pd.merge(exchanges, anns[["metabolite"]], on="reaction", how="left")
    exchanges["direction"] = DIRECTION[(exchanges.flux > 0.0).astype(int)].values
    exchanges = exchanges[exchanges.flux.abs() > exchanges.tolerance]

    return GrowthResults(growth, exchanges, anns)