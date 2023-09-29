import types as pytypes
import logging
import ontoweaver

from typing import Optional
from collections.abc import Iterable

import pandas as pd

from . import types

# Example of a simple configuration for extracting Oncodash' OncoKB tables.
example_configuration = {
    "row": "variant", # or line, entry, subject
    "columns": { # or fields
        "patient_id" : {
            "to_target"  : "patient", # Needs a valid "edge". # or to_node, to_object
            # "source" is always taken from "row".
            "via_edge" : "patient_has_target", # or via_relation, via_predicate
            # "properties": {}, # Does not map to any property.
        },
        "referenceGenome": {
            "to_target": "genome",
            "via_edge"  : "reference_genome",
        },
        "lastUpdate": {
            # Does not map to any target or edge.
            "to_properties": {
                "timestamp" : [
                    "variant",
                    "patient",
                    "genome",
                ],
            },
        },
    },
}

def extract_all(df: pd.DataFrame, config: dict):
    """Proxy function for extracting from a table all nodes, edges and properties
    that are defined in a PandasAdapter configuration."""
    mapping = ontoweaver.tabular.PandasAdapter.configure(config, ontoweaver.types)
    assert("variant" in dir(ontoweaver.types))

    allowed_node_types  = ontoweaver.types.all.nodes()
    logging.debug(f"allowed_node_types: {allowed_node_types}")

    allowed_node_fields = ontoweaver.types.all.node_fields()
    logging.debug(f"allowed_node_fields: {allowed_node_fields}")

    allowed_edge_types  = ontoweaver.types.all.edges()
    logging.debug(f"allowed_edge_types: {allowed_edge_types}")

    allowed_edge_fields = ontoweaver.types.all.edge_fields()
    logging.debug(f"allowed_edge_fields: {allowed_edge_fields}")

    # Using empty list or no argument would also select everything,
    # but explicit is better than implicit.
    oncokb = ontoweaver.tabular.PandasAdapter(
        df,
        *mapping,
        allowed_node_types,
        allowed_node_fields,
        allowed_edge_types,
        allowed_edge_fields,
    )

    return oncokb


class OncoKBExample(ontoweaver.tabular.PandasAdapter):
    """Example of an adapter holding a simple configuration for extracting Oncodash' OncoKB tables.
    """
    def __init__(self,
        df: pd.DataFrame,
        node_types : Optional[Iterable[ontoweaver.Node]] = None,
        node_fields: Optional[list[str]] = None,
        edge_types : Optional[Iterable[ontoweaver.Edge]] = None,
        edge_fields: Optional[list[str]] = None,
    ):

        # Type of the node created for each row.
        row_type = types.Target

        # Column name in table => relation type in KG.
        type_of = {
            "patient_id": types.Patient_has_target,
            "referenceGenome": types.Reference_genome,
        }

        # Any Element type in KB => list of columns to extract as properties.
        properties_of = {
            types.Patient: {"lastUpdate": "timestamp"},
            types.Target:  {"lastUpdate": "timestamp"},
            types.Genome:  {"lastUpdate": "timestamp"},
            types.Reference_genome:   {},
            types.Patient_has_target: {},
        }

        super().__init__(df, row_type, type_of, properties_of, node_types, node_fields, edge_types, edge_fields)

        self.run()
