import logging
import ontoweaver

from typing import Optional
from collections.abc import Iterable

import pandas as pd

from . import types

class OncoKB(ontoweaver.Adapter):

    def __init__(self,
        df: pd.DataFrame,
        node_types : Optional[Iterable[ontoweaver.Node]] = None,
        node_fields: Optional[list[str]] = None,
        edge_types : Optional[Iterable[ontoweaver.Edge]] = None,
        edge_fields: Optional[list[str]] = None,
    ):
        super().__init__(node_types, node_fields, edge_types, edge_fields)

        logging.info(df.info())
        logging.info(df)
        self.df = df

        # Column name in table => relation type in KG.
        self.type_of = {
            "patient_id": types.Patient_has_target,
            "referenceGenome": types.Reference_genome,
        }

        self.properties_of = {
            types.Patient: {"lastUpdate": "timestamp"},
            types.Target: {"lastUpdate": "timestamp"},
            types.Genome: {"lastUpdate": "timestamp"},
            types.Reference_genome:   {"lastUpdate": "timestamp"},
            types.Patient_has_target: {"lastUpdate": "timestamp"},
        }

        self.run()

    def properties(self, row, type):
        properties = {}
        matching_class = None
        for parent in type.mro():
            if parent in self.properties_of:
                matching_class = parent
                break
        if not matching_class:
            raise TypeError(f"Type `{type.__name__}` has no parent in properties mapping.")

        for in_prop in self.properties_of[matching_class]:
            out_prop = self.properties_of[type][in_prop]
            properties[out_prop] = row[in_prop]

        return properties

    def run(self):

        for i,row in self.df.iterrows():
            if self.allows( types.Target ):
                target_id = f"{types.Target.__name__}_{i}"
                # TODO: modularize an Adapter subclass for table data, and avoid duplicating type twice.
                self.nodes_append( self.make( types.Target, id=target_id, properties=self.properties(row,types.Target) ) )

            for k in self.type_of:
                assert(k in row)
                val = row[k]
                if self.allows( self.type_of[k] ):
                    # target should alway be the target above.
                    assert(issubclass(self.type_of[k].target_type(), types.Target))
                    # source:
                    st = self.type_of[k].source_type()
                    source_id = f"{st.__name__}_{val}"
                    self.nodes_append( self.make( st, id=source_id, properties=self.properties(row,st) ) )
                    # relation (simpler without property?)
                    self.edges_append( self.make( self.type_of[k], id=None, id_source=source_id, id_target=target_id, properties={} ) )

