from collections.abc import Iterable
from abc import ABCMeta as ABSTRACT
from abc import abstractmethod as abstract
from typing import TypeAlias
from typing import Optional

NodeTuple: TypeAlias = tuple[str,str,dict[str,str]]
class Node:

    def __init__(self,
        allowed_fields: list[str],
        id            : Optional[str] = None,
        label         : Optional[str] = "",
        properties    : Optional[dict[str,str]] = {}
    ):
        self._fields = allowed_fields
        self._id = id
        self._label = label
        self._properties = properties

    @property
    def fields(self):
        return self._fields

    @property
    def id(self):
        return self._id

    @property
    def label(self):
        return self._label

    @property
    def properties(self):
        return self._properties

    def as_tuple(self) -> NodeTuple:
        return (self._id, self._label, self._properties)

class Edge:
    pass


class Adapter(metaclass = ABSTRACT):

    def __init__(self,
        node_types,
        node_fields,
        edge_types,
    ):
        self._node_types  = node_types
        self._node_fields = node_fields
        self._edge_types  = edge_types

    @abstract
    def nodes(self) -> Iterable[Node]:
        raise NotImplementedError

    @abstract
    def edges(self) -> Iterable[Edge]:
        raise NotImplementedError


    @property
    def node_types(self):
        return self._node_types

    def allows(self, node_type: Node):
        return any(issubclass(n, node_type) for n in self._node_types)

    @property
    def node_fields(self):
        return self._node_fields

    @property
    def edge_types(self):
        return self._edge_types

