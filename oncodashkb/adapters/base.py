from collections.abc import Iterable
from abc import ABCMeta as ABSTRACT
from abc import abstractmethod as abstract
from typing import TypeAlias
from typing import Optional
from enum import Enum

class Node(metaclass = ABSTRACT):

    def __init__(self,
        id        : Optional[str] = None,
        properties: Optional[dict[str,str]] = {},
        allowed   : Optional[list[str]] = None,
        label     : Optional[str] = None,
    ):
        """Instantiate a node.

        :param str id: Unique identifier of the node. If id == None, is then set to the empty string.
        :param dict[str,str]: All available properties for this instance.
        :param list[str]: Allowed property names (the ones that will be exported to the knowledge graph by Biocypher). If allowed == None, all properties are allowed.
        :param str: The label of the node. If label = None, the lower-case version of the class name is used as a label.
        """
        if not id:
            self._id = ''
        else:
            self._id = id

        self._properties = properties
        # Sanity checks:
        for p in self._properties:
            assert(p in self.fields())

        if not allowed:
            self._allowed = self.fields()
        else:
            self._allowed = allowed
        # Sanity checks:
        for a in self._allowed:
            assert(a in self.fields())

        if not label:
            self._label = self.__class__.__name__.lower()
        else:
            self._label = label

    @staticmethod
    @abstract
    def fields() -> list[str]:
        """List of property fields provided by the (sub)class."""
        raise NotImplementedError

    @property
    def id(self) -> str:
        return self._id

    @property
    def label(self) -> str:
        return self._label

    @property
    def properties(self) -> dict[str,str]:
        return self._properties

    @property
    def allowed(self) -> list[str]:
        return self._allowed

    Tuple: TypeAlias = tuple[str,str,dict[str,str]]
    def as_tuple(self) -> Tuple:
        """Convert the class into Biocypher's expected tuple.

        Filter out properties along the way.
        """
        return (
            self._id,
            self._label,
            # Only keep properties that are allowed.
            {k:self._properties[k] for k in self._properties if k in self._allowed}
        )

class Edge:
    pass


class Adapter(metaclass = ABSTRACT):

    def __init__(self,
        node_types : Iterable[Node],
        node_fields: list,
        edge_types : Iterable[Edge],
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
    def node_types(self) -> Iterable[Node]:
        return self._node_types

    def allows(self, node_type: Node) -> bool:
        return any(issubclass(n, node_type) for n in self._node_types)

    @property
    def node_fields(self):
        return self._node_fields

    @property
    def edge_types(self) -> Iterable[Edge]:
        return self._edge_types

