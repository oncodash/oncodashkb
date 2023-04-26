from typing import Optional
from collections.abc import Iterable

from . import base
from . import types

class OncoKB(base.Adapter):

    def __init__(self,
        node_types : Optional[list] = None,
        node_fields: Optional[list] = None,
        edge_types : Optional[list] = None,
    ):
        super().__init__(node_types, node_fields, edge_types)

    def nodes(self) -> Iterable[base.NodeTuple]:
        if self.allows(types.Patient):
            yield types.Patient("id_node_1", "label_1", {}).as_tuple()
            yield ("id_node_2", "label_2", {})

    def edges(self):
        yield ("id_rel", "id_node_1", "id_node_2", "edge_type", {})

