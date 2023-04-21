from abc import ABCMeta as ABSTRACT
from abc import abstractmethod as abstract

class Adapter(metaclass = ABSTRACT):

    def __init__(self, 
        node_types: Optional[list] = None,
        node_fields: Optional[list] = None,
        edge_types: Optional[list] = None,
    ):
        self._node_types = node_types
        self._node_fields = node_fields
        self._edge_types = edge_types

    @abstract
    def nodes(self):
        raise NotImplementedError

    @abstract
    def edges(self):
        raise NotImplementedError

    @property
    def node_types(self):
        return self._node_types

    @property
    def node_fields(self):
        return self._node_fields

    @property
    def edge_types(self):
        return self._edge_types


class Node:

    def __init__(self):
        self._id = None
        self._label = None
        self._properties = {}

    @property
    def id(self):
        return self._id

    @property
    def label(self):
        return self._label

    @property
    def properties(self):
        return self._properties

