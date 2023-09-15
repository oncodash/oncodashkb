import sys
from typing import TypeAlias
from typing import Optional
from enum import Enum
from enum import auto

import ontoweaver

# Intermediate classes to add common fields.

class Item(ontoweaver.Node):

    @staticmethod
    def fields() -> list[str]:
        return [ "timestamp" ]

class Relation(ontoweaver.Edge):

    @staticmethod
    def fields() -> list[str]:
        return [ "timestamp" ]

# Actual classes.

class Patient(Item):

    @staticmethod
    def fields() -> list[str]:
        return [ "age" ]


class Target(Item):

    @staticmethod
    def fields() -> list[str]:
        return []


class Patient_has_target(Relation):

    @staticmethod
    def source_type():
        return Patient

    @staticmethod
    def target_type():
        return Target

    @staticmethod
    def fields() -> list[str]:
        return []


class Genome(Item):

    @staticmethod
    def fields() -> list[str]:
        return [ "age" ]


class Reference_genome(Relation):

    @staticmethod
    def source_type():
        return Genome

    @staticmethod
    def target_type():
        return Target

    @staticmethod
    def fields() -> list[str]:
        return []


# Allow accessing all ontoweaver.Item classes defined in this module.
all = ontoweaver.All(sys.modules[__name__])
