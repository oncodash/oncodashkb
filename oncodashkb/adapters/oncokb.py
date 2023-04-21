
class OncoKB(Adapter):

    def __init__(self,
        node_types: Optional[list] = None,
        node_fields: Optional[list] = None,
        edge_types: Optional[list] = None,
    ):
        super().__init__(self, node_types, node_fields, edge_types)

    def nodes(self):
        yield ("id_node_1", "label_1", {})
        yield ("id_node_2", "label_2", {})

    def edges(self):
        yield ("id_rel", "id_node_1", "id_node_2", "edge_type", {})

