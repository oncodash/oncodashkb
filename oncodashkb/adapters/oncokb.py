from typing import Optional
from collections.abc import Iterable

from . import base
from . import types

class OncoKB(base.Adapter):

    def __init__(self,
        node_types : Optional[Iterable[base.Node]] = None,
        node_fields: Optional[list[str]] = None,
        edge_types : Optional[Iterable[base.Edge]] = None,
        edge_fields: Optional[list[str]] = None,
    ):
        super().__init__(node_types, node_fields, edge_types, edge_fields)

    def nodes(self) -> Iterable[base.Node.Tuple]:

        if self.allows( types.Patient ):
            yield types.Patient(
                "patient_1", {"age": 42},
                self.node_fields ).as_tuple()
            yield types.Patient(
                "patient_2", {"age": 666},
                self.node_fields ).as_tuple()

        if self.allows( types.Target ):
            yield types.Target(
                "target_A", {},
                self.node_fields ).as_tuple()

    def edges(self) -> Iterable[base.Edge.Tuple]:

        if self.allows( types.Patient_has_target ):
            yield types.Patient_has_target(
                "rel_1", "patient_1", "target_A",
                self.edge_fields ).as_tuple()

