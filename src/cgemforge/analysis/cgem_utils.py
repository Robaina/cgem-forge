from typing import Union, Dict, List, Optional
from micom import Community
import copy

def get_growth_reactions(community: Community, growth_pattern: str = "growth") -> List[str]:
    """
    Find all growth reactions in a MICOM community model.
    
    Parameters
    ----------
    community : Community
        The MICOM community model
    growth_pattern : str, default "growth"
        Pattern to search for in reaction IDs to identify growth reactions.
        This can be customized for different naming conventions.
        
    Returns
    -------
    List[str]
        List of reaction IDs corresponding to growth/biomass reactions
    
    Examples
    --------
    # Default pattern ("growth")
    growth_rxns = get_growth_reactions(community_model)
    
    # Custom pattern for models using "biomass" in reaction names
    growth_rxns = get_growth_reactions(community_model, growth_pattern="biomass")
    """
    return [r.id for r in community.reactions if growth_pattern.lower() in r.id.lower()]


def set_minimal_growth_requirements(
    community: Community,
    cutoffs: Union[float, Dict[str, float]],
    growth_reactions: Optional[List[str]] = None,
    growth_pattern: str = "growth",
    inplace: bool = True
) -> Optional[Community]:
    """
    Set minimal positive flux values for growth reactions in a community model.
    
    This function allows setting lower bounds on growth reactions to guarantee
    individual growth for each taxon in the community. The cutoffs can be either
    a single value applied to all taxa or specific values for each taxon.
    
    Parameters
    ----------
    community : Community
        The MICOM community model to modify
    cutoffs : Union[float, Dict[str, float]]
        Either a single float value to apply to all growth reactions,
        or a dictionary mapping reaction IDs to their specific cutoff values.
        A cutoff of 0 means no minimal growth requirement.
    growth_reactions : Optional[List[str]], default None
        List of reaction IDs corresponding to growth/biomass reactions.
        If None, growth reactions will be identified automatically using growth_pattern.
    growth_pattern : str, default "growth"
        Pattern to search for in reaction IDs to identify growth reactions.
        Only used if growth_reactions is None.
    inplace : bool, default True
        Whether to modify the community model in place or return a copy
        
    Returns
    -------
    Optional[Community]
        If inplace=False, returns the modified community model.
        Otherwise, returns None and modifies the input community model.
        
    Examples
    --------
    # Set a single cutoff for all taxa using automatic reaction detection
    set_minimal_growth_requirements(community, 0.01)
    
    # Use a different pattern to identify growth reactions
    set_minimal_growth_requirements(community, 0.01, growth_pattern="biomass")
    
    # Set specific cutoffs for each taxon
    specific_cutoffs = {
        "species_1_growth": 0.05,
        "species_2_growth": 0.02,
        "species_3_growth": 0.0   # No growth requirement
    }
    set_minimal_growth_requirements(community, specific_cutoffs)
    
    # Provide explicit list of growth reactions
    growth_rxns = ["rxn1", "rxn2", "rxn3"]
    set_minimal_growth_requirements(community, 0.01, growth_reactions=growth_rxns)
    """
    # Make a copy if not modifying in place
    if not inplace:
        community = copy.deepcopy(community)
    
    # If growth_reactions is not provided, find them using the pattern
    if growth_reactions is None:
        growth_reactions = get_growth_reactions(community, growth_pattern)
        
    if not growth_reactions:
        raise ValueError(
            f"No growth reactions found with pattern '{growth_pattern}'. "
            "Please check the pattern or provide explicit growth_reactions."
        )
    
    # Handle single cutoff value case
    if isinstance(cutoffs, (int, float)):
        cutoff_dict = {rxn_id: cutoffs for rxn_id in growth_reactions}
    else:
        cutoff_dict = cutoffs
        
    # Validate that all growth reactions have cutoffs if a dictionary was provided
    if not isinstance(cutoffs, (int, float)):
        missing_rxns = set(growth_reactions) - set(cutoff_dict.keys())
        if missing_rxns:
            raise ValueError(
                f"The following growth reactions don't have specified cutoffs: {missing_rxns}"
            )
    
    # Validate that all provided reactions exist in the model
    invalid_rxns = set(growth_reactions) - {r.id for r in community.reactions}
    if invalid_rxns:
        raise ValueError(
            f"The following reaction IDs don't exist in the model: {invalid_rxns}"
        )
    
    # Set lower bounds for growth reactions
    for rxn_id, cutoff in cutoff_dict.items():
        if rxn_id in growth_reactions:
            reaction = community.reactions.get_by_id(rxn_id)
            reaction.lower_bound = cutoff
    
    # If not modifying in place, return the modified model
    if not inplace:
        return community
    return None

def reset_growth_requirements(
    community: Community,
    growth_reactions: Optional[List[str]] = None,
    growth_pattern: str = "growth",
    inplace: bool = True
) -> Optional[Community]:
    """
    Reset all growth reaction lower bounds to zero in a community model.
    
    This function removes any minimal growth requirements previously set,
    allowing for unconstrained solutions.
    
    Parameters
    ----------
    community : Community
        The MICOM community model to modify
    growth_reactions : Optional[List[str]], default None
        List of reaction IDs corresponding to growth/biomass reactions.
        If None, growth reactions will be identified automatically using growth_pattern.
    growth_pattern : str, default "growth"
        Pattern to search for in reaction IDs to identify growth reactions.
        Only used if growth_reactions is None.
    inplace : bool, default True
        Whether to modify the community model in place or return a copy
        
    Returns
    -------
    Optional[Community]
        If inplace=False, returns the modified community model.
        Otherwise, returns None and modifies the input community model.
        
    Examples
    --------
    # Reset all automatically detected growth reactions
    reset_growth_requirements(community)
    
    # Using a custom pattern to identify growth reactions
    reset_growth_requirements(community, growth_pattern="biomass")
    
    # Explicitly providing growth reactions
    growth_rxns = ["org1_growth", "org2_growth", "org3_growth"]
    reset_growth_requirements(community, growth_reactions=growth_rxns)
    """
    # Make a copy if not modifying in place
    if not inplace:
        community = community.copy()
    
    # If growth_reactions is not provided, find them using the pattern
    if growth_reactions is None:
        growth_reactions = get_growth_reactions(community, growth_pattern)
        
    if not growth_reactions:
        raise ValueError(
            f"No growth reactions found with pattern '{growth_pattern}'. "
            "Please check the pattern or provide explicit growth_reactions."
        )
    
    # Validate that all provided reactions exist in the model
    invalid_rxns = set(growth_reactions) - {r.id for r in community.reactions}
    if invalid_rxns:
        raise ValueError(
            f"The following reaction IDs don't exist in the model: {invalid_rxns}"
        )
    
    # Reset lower bounds for all growth reactions to 0
    for rxn_id in growth_reactions:
        reaction = community.reactions.get_by_id(rxn_id)
        reaction.lower_bound = 0.0
    
    # If not modifying in place, return the modified model
    if not inplace:
        return community
    return None