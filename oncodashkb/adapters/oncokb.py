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

        print(df)
        self.df = df

        self.mapping = {
            "patient_id": types.Patient_has_target,
            "referenceGenome": types.Reference_genome,
        }

        self._nodes = []
        self._edges = []

        self.run()

    def run(self):

        for i,row in self.df.iterrows():
            if self.allows( types.Target ):
                target_id = f"target_{i}"
                self._nodes.append( self.make( types.Target, target_id, {} ) )

            for k,val in row.items():
                if k in self.mapping:
                    # print(k, "=>", self.mapping[k].__name__, end = " ")
                    # print("(", self.mapping[k].source_type().__name__, "<->", self.mapping[k].target_type().__name__, ")")
                    if self.allows( self.mapping[k] ):
                        # target should alway be the target above.
                        assert(issubclass(self.mapping[k].target_type(), types.Target))
                        # source:
                        self._nodes.append( self.make( self.mapping[k].source_type(), val, {} ) )
                        # relation
                        self._edges.append( self.make( self.mapping[k], None, val, target_id, {} ) )


    def nodes(self) -> Iterable[base.Node.Tuple]:
        for n in self._nodes:
            yield n

    def edges(self) -> Iterable[base.Edge.Tuple]:
        for e in self._edges:
            yield e


