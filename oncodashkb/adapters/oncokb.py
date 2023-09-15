import types as pytypes
import logging
import ontoweaver

from typing import Optional
from collections.abc import Iterable

import pandas as pd

from . import types

def parse_all(df):

    configure = ontoweaver.tabular.Configure( {
        "row": "Target", # line, entry
        "columns": { # fields
            "patient_id" : {
                "to_target"  : "Patient", # Needs a valid "edge". # to_node, to_object
                # "source" is always taken from "row".
                "via_edge" : "Patient_has_target", # via_relation, via_predicate
                # "properties": {}, # Does not map to any property.
            },
            "referenceGenome": {
                "to_target": "Genome",
                "via_edge"  : "Reference_genome",
            },
            "lastUpdate": {
                # Does not map to any target or edge.
                "to_properties": {
                    "timestamp" : [
                        "Target",
                        "Patient",
                        "Genome",
                    ],
                },
            },
        },
    },
    ontoweaver.types)

    mapping = configure.parse()
    assert("Target" in dir(ontoweaver.types))

    allowed_node_types  = ontoweaver.types.all.nodes()
    # print("allowed_node_types:", allowed_node_types)

    allowed_node_fields = ontoweaver.types.all.node_fields()
    # print("allowed_node_fields:", allowed_node_fields)

    allowed_edge_types  = ontoweaver.types.all.edges()
    # print("allowed_edge_types:", allowed_edge_types)

    allowed_edge_fields = ontoweaver.types.all.edge_fields()
    # print("allowed_edge_fields:", allowed_edge_fields)

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


class OncoKB(ontoweaver.tabular.PandasAdapter):

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
