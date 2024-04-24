from __future__ import annotations
from pathlib import Path

import pandas as pd
import cobra
from cobra import Reaction, Model

import phycogem.reconstruction_helpers as helpers


class GEM:
    """Store and manipulate a genome-scale metabolic self._model."""

    def __init__(self, model: Path):
        self._model = cobra.io.read_sbml_model(model)

    def _repr_html_(self):
        return self._model._repr_html_()

    @property
    def model(self) -> Model:
        """Return cobrapy model object."""
        return self._model

    def write(self, output_path: Path) -> None:
        """Write model to file."""
        cobra.io.write_sbml_model(self._model, output_path)

    def remove_shuttle_reactions(
        self, allowed_compartments: set = {"c", "e", "p"}
    ) -> None:
        """
        Remove shuttle reactions between unwanted compartments.

        Args:
            model (Model): _description_
            allowed_compartments (set, optional): _description_. Defaults to {"c", "e", "p"}.
        """
        shuttle_rxns_in_unwanted_compartments = [
            rxn
            for rxn in self._model.reactions
            if (
                (len(rxn.compartments) > 1)
                and (not rxn.compartments.issubset(allowed_compartments))
            )
        ]
        self._model.remove_reactions(
            shuttle_rxns_in_unwanted_compartments, remove_orphans=True
        )

    def move_reactions_to_cytoplasm(
        self, allowed_compartments: set = {"c", "e", "p"}
    ) -> None:
        """
        Update the metabolites of a reaction to include a new set of metabolites
        Args:
            reaction (Reaction): _description_
            allowed_compartments (set, optional): _description_. Defaults to {"c", "e", "p"}.
        """
        reactions_to_add = []
        reactions_to_remove = []
        for reaction in self._model.reactions:
            if not reaction.compartments.issubset(allowed_compartments):

                new_metabolites = {}
                for metabolite, stoich in reaction.metabolites.items():
                    new_met_id = metabolite.id[:-1] + "c"
                    new_metabolite = (
                        self._model.metabolites.get_by_id(new_met_id)
                        if new_met_id in self._model.metabolites
                        else metabolite.copy()
                    )
                    new_metabolite.compartment = "c"
                    new_metabolite.id = new_met_id
                    if new_met_id not in self._model.metabolites:
                        self._model.add_metabolites([new_metabolite])
                        self._model.remove_metabolites([metabolite])
                    new_metabolites[new_metabolite] = stoich

                new_reaction = Reaction(
                    id=reaction.id,
                    name=reaction.name,
                    lower_bound=reaction.lower_bound,
                    upper_bound=reaction.upper_bound,
                    subsystem=reaction.subsystem,
                )
                new_reaction.gene_reaction_rule = reaction.gene_reaction_rule
                new_reaction.add_metabolites(new_metabolites)
                reactions_to_add.append(new_reaction)
                reactions_to_remove.append(reaction)

        self._model.remove_reactions(reactions_to_remove, remove_orphans=True)
        self._model.add_reactions(reactions_to_add)

    def annotate_compounds(self, cpd_annotations: Path) -> None:
        """
        Annotate compounds in model: chemical formulae and charge

        Args:
            model (Model): _description_
            cpd_annotations (Path): _description_
        """
        cpd_db = pd.read_csv(cpd_annotations, sep="\t", index_col=0)
        for met in self._model.metabolites:
            met_id = helpers.remove_compartment(met.id)
            if met_id in cpd_db.index:
                met.formula = cpd_db.loc[met_id, "formula"]
                met.charge = cpd_db.loc[met_id, "charge"]

    def prepare_for_carveme(self, output_reaction_file: Path) -> None:
        """
        Prepare model for carveme universe curation pipeline.
        (This is a provisional fix to avoid modiying CarveME source code)
        1. Change compartment name to 'C_' format
        2. Generate model specific reaction list csv file
        """
        for met in self._model.metabolites:
            if not met.compartment.startswith("C_"):
                met.compartment = f"C_{met.compartment}"

        data = []
        for rxn in self._model.reactions:
            data.append(
                [
                    "iML1515",
                    rxn.id,
                    rxn.lower_bound,
                    rxn.upper_bound,
                    rxn.subsystem,
                    rxn.gene_reaction_rule,
                ]
            )
        df = pd.DataFrame(
            data, columns=["model", "reaction", "lb", "ub", "subsystem", "gpr"]
        )
        df.to_csv(output_reaction_file, index=False)

    def open_exchanges(self) -> None:
        """
        Open all exchanges in a self._model.

        Args:
            model (Model): a cobra model object

        Returns:
            Model: a cobra model object with all exchanges open
        """
        for exchange in self._model.exchanges:
            exchange.lower_bound = -1000

    def close_exchanges(self) -> None:
        """
        Close all exchange reactions in a model.

        Args:
            model (Model): _description_
        """
        for rxn in self._model.reactions:
            if rxn.id.startswith("EX_"):
                rxn.lower_bound = 0

    def remove_duplicated_reactions(self, duplicated_reactions: list[list]) -> None:
        """Remove duplicated reactions from model

        Args:
            duplicated_reactions (list[list]):list lists of duplicated pairs
        """
        reactions_to_remove = [rxn_pair[0] for rxn_pair in duplicated_reactions]
        self._model.remove_reactions(reactions_to_remove, remove_orphans=True)

    def get_organic_exchanges(self) -> list[str]:
        """
        Get IDs of all organic exchanges in a self._model.
        Returns:
            list. List of exchange IDs.
        """
        organic_exchanges = []
        for rxn in self._model.exchanges:
            met = [met for met in rxn.metabolites][0]
            if met.formula is not None:
                chemical_elements = helpers.extract_chemical_elements(met.formula)
                if (
                    (not helpers.is_co2(chemical_elements))
                    and (not helpers.is_hco3(chemical_elements))
                    and ("C" in chemical_elements)
                ):
                    organic_exchanges.append(rxn.id)
        return organic_exchanges

    def get_inorganic_exchanges(self) -> list[str]:
        """
        Get IDs of all inorganic exchanges in a model.
        Returns:
            list. List of exchange IDs.
        """
        inorganic_exchanges = []
        for rxn in self._model.exchanges:
            met = [met for met in rxn.metabolites][0]
            if met.formula is not None:
                chemical_elements = helpers.extract_chemical_elements(met.formula)
                if (
                    (helpers.is_co2(chemical_elements))
                    or (helpers.is_hco3(chemical_elements))
                    or ("C" not in chemical_elements)
                ):
                    inorganic_exchanges.append(rxn.id)
        return inorganic_exchanges

    def open_inorganic_exchanges(
        self,
        lower_bound: float = -1000,
        upper_bound: float = 1000,
        include: list = None,
    ) -> None:
        """
        Open all inorganic exchanges in a model and close organic exchanges,
        except for indicated ones.

        Args:
            lower_bound : float, optional
            upper_bound : float, optional
            include: list, optional, List of exchange IDs to be opened besides
            inorganic ones. Default is None.
        """
        for rxn in self._model.exchanges:
            if include is not None and rxn.id in include:
                rxn.lower_bound = lower_bound
                rxn.upper_bound = upper_bound
            else:
                met = [met for met in rxn.metabolites][0]
                if met.formula is not None:
                    chemical_elements = helpers.extract_chemical_elements(met.formula)
                    if "C" not in chemical_elements:
                        rxn.lower_bound = lower_bound
                        rxn.upper_bound = upper_bound
                    else:
                        rxn.lower_bound = 0

    def add_external_metabolite(self, met_id: str) -> None:
        """
        Add an external metabolite to a self._model.

        Args:
            met_id (str): _description_

        Returns:
            Model: _description_
        """
        met = self._model.metabolites.get_by_id(met_id)
        met_to_add = met.copy()
        met_to_add.id = met_id[:-2] + "_e"
        met_to_add.compartment = "e"
        self._model.add_metabolites([met_to_add])

    def add_transport_reaction(
        self,
        met_i: str,
        met_j: str,
        lower_bound: float = -1000.0,
        upper_bound: float = 1000.0,
    ) -> None:
        """
        Add a transport reaction to a self._model.

        Args:
            met (Metabolite): _description_
            met_to_add (Metabolite): _description_

        Returns:
            Model: _description_
        """
        met = self._model.metabolites.get_by_id(met_i)
        met_to_add = self._model.metabolites.get_by_id(met_j)
        rxn_id = f"TR_{met.id}_to_{met_to_add.id}"
        rxn = Reaction(rxn_id)
        rxn.name = f"Transport of {met.id} to {met_to_add.id}"
        rxn.add_metabolites({met: -1, met_to_add: 1})
        rxn.lower_bound = lower_bound
        rxn.upper_bound = upper_bound
        rxn.subsystem = "Transport"
        rxn.gene_reaction_rule = "Spontaenous"
        self._model.add_reactions([rxn])

    def add_exchanges_for_metabolites(self, met_ids: list[str]) -> None:
        """
        Add exchange reactions for a list of metabolites.

        Args:
            met_ids (list[str]): _description_

        Returns:
            Model: _description_
        """
        for met_id in met_ids:
            if met_id in self._model.metabolites:
                met = self._model.metabolites.get_by_id(met_id)
                if met.compartment != "e":
                    model = self.add_external_metabolite(model, met_id)
                    model = self.add_transport_reaction(model, met.id, met_to_add.id)
                else:
                    met_to_add = met
                self._model.add_boundary(met_to_add, type="exchange")
            else:
                print(f"Metabolite {met_id} not found in self._model.")

    def set_medium(
        self, medium_id: str, media_db: Path, energy_source: tuple[str, float] = None
    ) -> None:
        """
        Set the medium for a model.

        Args:
            medium_id (str): _description_
            media_db (Path): _description_
            energy_source (tuple[str, float]): _description_
        """
        self.close_exchanges()
        medium_dict = {
            rxn_id: flux
            for rxn_id, flux in helpers.get_medium_dict_from_media_db(
                media_db, medium_id
            ).items()
            if rxn_id in self._model.exchanges
        }

        if energy_source is not None:
            if energy_source[0] in self._model.exchanges:
                medium_dict[energy_source[0]] = energy_source[1]
            else:
                print(f"Carbon source {energy_source[0]} not found in model.")
        self._model.medium = medium_dict

    def rescale_fluxes(self, maximum_flux: float = 1000.0) -> None:
        """
        Rescale maximum fluxes of all reactions in a self._model.

        Args:
            model (Model): _description_
            max_flux (float, optional): _description_. Defaults to 1000.0.
        """
        max_abs_flux = max(
            [abs(rxn.upper_bound) for rxn in self._model.reactions]
            + [abs(rxn.lower_bound) for rxn in self._model.reactions]
        )
        for rxn in self._model.reactions:
            rxn.upper_bound = maximum_flux * (rxn.upper_bound / max_abs_flux)
            rxn.lower_bound = maximum_flux * (rxn.lower_bound / max_abs_flux)

    def remove_blocked_reactions(self) -> None:
        """
        Remove blocked reactions from a self._model.

        Args:
            model (Model): _description_
        """
        self._model.optimize()
        blocked_rxns = cobra.flux_analysis.variability.find_blocked_reactions(
            self._model
        )
        self._model.remove_reactions(blocked_rxns, remove_orphans=True)

    def compute_flux_ranges(self) -> pd.DataFrame:
        """
        Compute flux ranges for all reactions in a self._model.

        Args:
            model (Model): _description_
        """
        self._model.optimize()
        flux_ranges = cobra.flux_analysis.variability.flux_variability_analysis(
            self._model
        )
        return flux_ranges

    def sample_flux_space(
        self, n_samples: int = 1000, n_processes: int = None
    ) -> pd.DataFrame:
        """
        Sample the flux space of a self._model.

        Args:
            model (Model): _description_
            n_samples (int, optional): _description_. Defaults to 1000.

        Returns:
            DataFrame: _description_
        """
        if n_processes is None:
            n_processes = 2
        self._model.optimize()
        flux_samples = cobra.sampling.sample(
            self._model, n_samples, method="achr", processes=n_processes
        )
        return flux_samples
