from collections.abc import Iterable
from abc import ABCMeta as ABSTRACT
from abc import abstractmethod as abstract
from typing import TypeAlias
from typing import Optional
from enum import Enum

class Element(metaclass = ABSTRACT):

    def __init__(self,
        id        : Optional[str] = None,
        properties: Optional[dict[str,str]] = {},
        allowed   : Optional[list[str]] = None,
        label     : Optional[str] = None,
    ):
        """Instantiate an element.

        :param str id: Unique identifier of the node. If id == None, is then set to the empty string.
        :param dict[str,str]: All available properties for this instance.
        :param list[str]: Allowed property names (the ones that will be exported to the knowledge graph by Biocypher). If allowed == None, all properties are allowed.
        :param str: The label of the node. If label = None, the lower-case version of the class name is used as a label.
        """
        if not id:
            self._id = ''
        else:
            self._id = id

        # Use the setter to get sanity checks.
        self.properties = properties

        # Use the setter to get sanity checks.
        if not allowed:
            self.allowed = self.fields()
        else:
            self.allowed = allowed

        if not label:
            self._label = self.__class__.__name__.lower()
        else:
            self._label = label

    @staticmethod
    @abstract
    def fields() -> list[str]:
        """List of property fields provided by the (sub)class."""
        raise NotImplementedError

    @abstract
    def as_tuple(self):
        """Convert the element class into Biocypher's expected tuple.

        Filter out properties along the way.
        """
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

    @properties.setter
    def properties(self, properties: dict[str,str]):
        # Sanity checks:
        assert(properties is not None)
        for p in properties:
            assert(p in self.fields())
        self._properties = properties

    @property
    def allowed(self) -> list[str]:
        return self._allowed

    @allowed.setter
    def allowed(self, allowed_properties: list[str]):
        # Sanity checks:
        assert(allowed_properties is not None)
        for a in allowed_properties:
            assert(a in self.fields())
        self._allowed = allowed_properties

    def allowed_properties(self):
        """Filter out properties that are not allowed."""
        assert(self._properties is not None)
        assert(self._allowed is not None)
        return {k:self._properties[k] for k in self._properties if k in self._allowed}


class Node(Element):

    def __init__(self,
        id        : Optional[str] = None,
        properties: Optional[dict[str,str]] = {},
        allowed   : Optional[list[str]] = None,
        label     : Optional[str] = None,
    ):
        super().__init__(id, properties, allowed, label)

    Tuple: TypeAlias = tuple[str,str,dict[str,str]]
    def as_tuple(self) -> Tuple:
        return (
            self._id,
            self._label,
            # Only keep properties that are allowed.
            self.allowed_properties()
        )

class Edge(Element):

    def __init__(self,
        id        : Optional[str] = None,
        id_source : Optional[str] = None,
        id_target : Optional[str] = None,
        properties: Optional[dict[str,str]] = {},
        allowed   : Optional[list[str]] = None,
        label     : Optional[str] = None,
    ):
        super().__init__(id, properties, allowed, label)
        self._id_source  = id_source
        self._id_target = id_target

    @property
    def id_source(self):
        return self._id_source

    @property
    def id_target(self):
        return self._id_source

    Tuple: TypeAlias = tuple[str,str,str,dict[str,str]]
    def as_tuple(self) -> Tuple:
        return (
            self._id,
            self._id_source,
            self._id_target,
            self._label,
            # Only keep properties that are allowed.
            self.allowed_properties()
        )


class Adapter(metaclass = ABSTRACT):

    def __init__(self,
        node_types : Iterable[Node],
        node_fields: list[str],
        edge_types : Iterable[Edge],
        edge_fields: list[str],
    ):
        self._node_types  = node_types
        self._node_fields = node_fields
        self._edge_types  = edge_types
        self._edge_fields = edge_fields

    @abstract
    def nodes(self) -> Iterable[Node]:
        raise NotImplementedError

    @abstract
    def edges(self) -> Iterable[Edge]:
        raise NotImplementedError

    @property
    def node_types(self) -> Iterable[Node]:
        return self._node_types

    @property
    def node_fields(self) -> list[str]:
        return self._node_fields

    @property
    def edge_types(self) -> Iterable[Edge]:
        return self._edge_types

    @property
    def edge_fields(self) -> list[str]:
        return self._edge_fields

    def allows(self, elem_type: Element) -> bool:
        # FIXME: double-check if we want strict class equality or issubclass.
        if issubclass(elem_type, Node):
            return any(issubclass(e, elem_type) for e in self._node_types)
        elif issubclass(elem_type, Edge):
            return any(issubclass(e, elem_type) for e in self._edge_types)
        else:
            raise TypeError("`elem_type` should be of type `Element`")


class All:
    def __init__(self, module):
        self.module = module

    def elements(self, asked: Element = Element) -> list[Element]:
        m = self.module.__dict__
        classes = []
        for c in m:
            if isinstance(m[c], type) \
            and m[c].__module__ == self.module.__name__ \
            and issubclass(m[c], asked):
                classes.append(m[c])
        return classes

    def nodes(self) -> list[Node]:
        return self.elements(Node)

    def edges(self) -> list[Edge]:
        return self.elements(Edge)

    def node_fields(self) -> list[str]:
        names = []
        for c in self.nodes():
            names += c.fields()
        return names

    def edge_fields(self) -> list[str]:
        names = []
        for c in self.edges():
            names += c.fields()
        return names

