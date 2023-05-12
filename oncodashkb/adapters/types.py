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
        super().__init__(id, properties, allowed, label)

    @staticmethod
    def fields() -> list[str]:
        return []

