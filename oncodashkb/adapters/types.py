import sys
from typing import TypeAlias
from typing import Optional
from enum import Enum
from enum import auto

from . import base

class Patient(base.Node):

    def __init__(self,
        id            : Optional[str] = None,
        properties    : Optional[dict[str,str]] = {},
        allowed       : Optional[list[str]] = None,
        label         : Optional[str] = None,
    ):
        super().__init__(id, properties, allowed, label)

    @staticmethod
    def fields() -> list[str]:
        return [ "age" ]


class Target(base.Node):

    def __init__(self,
        id            : Optional[str] = None,
        properties    : Optional[dict[str,str]] = {},
        allowed       : Optional[list[str]] = None,
        label         : Optional[str] = None,
    ):
        super().__init__(id, properties, allowed, label)

    @staticmethod
    def fields() -> list[str]:
        return []


class Patient_has_target(base.Edge):

    def __init__(self,
        id        : Optional[str] = None,
        id_source : Optional[str] = None,
        id_target : Optional[str] = None,
        properties: Optional[dict[str,str]] = {},
        allowed   : Optional[list[str]] = None,
        label     : Optional[str] = None,
    ):
        super().__init__(id, id_source, id_target, properties, allowed, label)

    @staticmethod
    def fields() -> list[str]:
        return []


class all:
    @staticmethod
    def elements(asked: base.Element = base.Element) -> list[base.Element]:
        module = sys.modules[__name__]
        m = module.__dict__
        classes = []
        for c in m:
            if isinstance(m[c], type) \
            and m[c].__module__ == module.__name__ \
            and issubclass(m[c], asked):
                classes.append(m[c])
        return classes

    @staticmethod
    def nodes() -> list[base.Node]:
        return all.elements(base.Node)

    @staticmethod
    def edges() -> list[base.Edge]:
        return all.elements(base.Edge)

    @staticmethod
    def node_fields() -> list[str]:
        names = []
        for c in all.nodes():
            names += c.fields()
        return names

    @staticmethod
    def edge_fields() -> list[str]:
        names = []
        for c in all.edges():
            names += c.fields()
        return names


