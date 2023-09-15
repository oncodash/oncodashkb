import types as pytypes
import logging
import ontoweaver

from typing import Optional
from collections.abc import Iterable

import pandas as pd

from . import types

class OncoKBTable(ontoweaver.tabular.PandasAdapter):
    def __init__(self,
        df: pd.DataFrame,
        config: dict,
        node_types : Optional[Iterable[ontoweaver.Node]] = None,
        node_fields: Optional[list[str]] = None,
        edge_types : Optional[Iterable[ontoweaver.Edge]] = None,
        edge_fields: Optional[list[str]] = None,
    ):

        # graph_from_table = {
        #     "source": { # subject
        #         "class": "Target", # type
        #         "properties": [
        #             "timestamp": "lastUpdate",
        #         ],
        #     },
        #     "edges": { # relations, predicates
        #         "Patient_has_target": {
        #             "from_column": "patient_id",
        #             # "source" is always taken from "center".
        #             "target": {
        #                 "class": "Patient", # Needs a valid "column". # object, node
        #                 "properties": {
        #                     "timestamp": "lastUpdate",
        #                 },
        #             },
        #             # "properties": {}, # Does not map from any column.
        #         },
        #         "Reference_genome": {
        #             "column": "referenceGenome",
        #             "target": "Genome",
        #             "target_properties": [
        #                 "timestamp": "lastUpdate",
        #             ],
        #         },
        #     },
        # }

        self.config = {
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
        }

        source_t, type_of, properties_of = self.parse()
        logging.debug(f"Source class: {source_t}")
        logging.debug(f"Type_of: {type_of}")
        logging.debug(f"Properties_of: {properties_of}")

        super().__init__(df, source_t, type_of, properties_of, node_types, node_fields, edge_types, edge_fields)

        self.run()

    def get(self, key, config=None):
        if not config:
            config = self.config
        for k in key:
            if k in config:
                return config[k]
        return None

    def make_node(self, name, base = ontoweaver.Node):
        t = type(name, (base,), {"__module__": "ontoweaver.types"})
        def empty_fields():
            return []
        t.fields = staticmethod(pytypes.MethodType(empty_fields, t))
        logging.debug(f"Declare Node class `{t}`.")
        return t

    def make_edge(self, name, source_t, target_t, base = ontoweaver.Edge):
        t = type(name, (base,), {"__module__": "ontoweaver.types"})
        def empty_fields():
            return []
        t.fields = staticmethod(pytypes.MethodType(empty_fields, t))
        def st():
            return source_t
        def tt():
            return target_t
        t.source_type = staticmethod(pytypes.MethodType(st, t))
        t.target_type = staticmethod(pytypes.MethodType(tt, t))
        logging.debug(f"Declare Edge class `{t}`.")
        return t

    def parse(self):
        type_of = {}
        properties_of = {}

        k_row = ["row", "entry", "line"]
        k_columns = ["columns", "fields"]
        k_target = ["to_target", "to_object", "to_node"]
        k_edge = ["via_edge", "via_relation", "via_predicate"]
        k_properties = ["to_properties"]

        source_t = self.make_node( self.get(k_row) )

        columns = self.get(k_columns)
        for col_name in columns:
            column = columns[col_name]
            target     = self.get(k_target, column)
            edge       = self.get(k_edge, column)
            properties = self.get(k_properties, column)

            if target and edge:
                target_t = self.make_node( target )
                edge_t   = self.make_edge( edge, source_t, target_t )
                type_of[col_name] = edge_t # Embeds source and target types.

            if properties:
                for prop_name in properties:
                    types = properties[prop_name]
                    for t in types:
                        properties_of[t] = properties.get(t, {})
                        properties_of[t][col_name] = prop_name

        return source_t, type_of, properties_of


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
