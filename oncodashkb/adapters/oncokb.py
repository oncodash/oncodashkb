import logging

from typing import Optional
from collections.abc import Iterable

import pandas as pd

from . import base
from . import types

class OncoKB(base.Adapter):

    def __init__(self,
        df: pd.DataFrame,
        node_types : Optional[Iterable[base.Node]] = None,
        node_fields: Optional[list[str]] = None,
        edge_types : Optional[Iterable[base.Edge]] = None,
        edge_fields: Optional[list[str]] = None,
    ):
        super().__init__(node_types, node_fields, edge_types, edge_fields)

        logging.info(df.info())
        logging.info(df)
        self.df = df

        # Column name in table => relation type in KG.
        self.mapping = {
            "patient_id": types.Patient_has_target,
            "referenceGenome": types.Reference_genome,
        }

        self.run()

    def run(self):

        for i,row in self.df.iterrows():
            if self.allows( types.Target ):
                target_id = f"target_{i}"
                # TODO: extract metadata as properties (for ex. timestamps).
                self.nodes_append( self.make( types.Target, id=target_id, properties={} ) )

            for k in self.mapping:
                assert(k in row)
                val = row[k]
                if self.allows( self.mapping[k] ):
                    # target should alway be the target above.
                    assert(issubclass(self.mapping[k].target_type(), types.Target))
                    # source:
                    self.nodes_append( self.make( self.mapping[k].source_type(), id=val, properties={} ) )
                    # relation:
                    self.edges_append( self.make( self.mapping[k], id=None, id_source=val, id_target=target_id, properties={} ) )

