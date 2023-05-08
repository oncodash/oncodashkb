from typing import Optional
from collections.abc import Iterable

from . import base
from . import types

class OncoKB(base.Adapter):

    def __init__(self,
        node_types : Optional[Iterable[base.Node]] = None,
        node_fields: Optional[list[str]] = None,
        edge_types : Optional[Iterable[base.Edge]] = None,
    ):
        super().__init__(node_types, node_fields, edge_types)

    def nodes(self) -> Iterable[base.Node.Tuple]:
        if self.allows(types.Patient):
            yield types.Patient("id_node_1", {"age": 42}, self.node_fields).as_tuple()
            yield ("id_node_2", "patient", {})

    def edges(self):
        yield ("id_rel", "id_node_1", "id_node_2", "patient_to_patient", {})

