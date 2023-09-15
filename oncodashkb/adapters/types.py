import sys
from typing import TypeAlias
from typing import Optional
from enum import Enum
from enum import auto

import ontoweaver

class Patient(ontoweaver.Node):

    @staticmethod
    def fields() -> list[str]:
        return [ "age" ]


class Target(ontoweaver.Node):

    @staticmethod
    def fields() -> list[str]:
        return []


class Patient_has_target(ontoweaver.Edge):

    @staticmethod
    def source_type():
        return Patient

    @staticmethod
    def target_type():
        return Target

    @staticmethod
    def fields() -> list[str]:
        return []


class Genome(ontoweaver.Node):

    @staticmethod
    def fields() -> list[str]:
        return [ "age" ]


class Reference_genome(ontoweaver.Edge):

    @staticmethod
    def source_type():
        return Genome

    @staticmethod
    def target_type():
        return Target

    @staticmethod
    def fields() -> list[str]:
        return []


# Allow accessing all ontoweaver.Element classes defined in this module.
all = ontoweaver.All(sys.modules[__name__])
