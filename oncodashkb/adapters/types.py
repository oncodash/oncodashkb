import sys
from typing import TypeAlias
from typing import Optional
from enum import Enum
from enum import auto

import ontoweaver

class sample(ontoweaver.Node):
    @staticmethod
    def fields():
        return []

class patient(ontoweaver.Node):
    @staticmethod
    def fields():
        return ["cohort_code", "survival"]

class sample_to_patient(ontoweaver.Edge):
    @staticmethod
    def source_type():
        return sample

    @staticmethod
    def target_type():
        return patient

    @staticmethod
    def fields():
        return []

# The `variant` class is declared through the config file, along with its properties.
class variant(ontoweaver.Node):
    @staticmethod
    def fields():
        return ["timestamp", "version", "mutation_effect_description", "variant_summary"]

class annotation(ontoweaver.Node):
    @staticmethod
    def fields():
        return []


class DB_Object_Symbol(ontoweaver.Node):
    @staticmethod
    def fields():
        return []

class GO_involved_in(ontoweaver.Node):
    @staticmethod
    def fields():
        return []

class GO_enables(ontoweaver.Node):
    @staticmethod
    def fields():
        return []
class gene_to_biological_process(ontoweaver.Edge):
    @staticmethod
    def source_type():
        return DB_Object_Symbol

    @staticmethod
    def target_type():
        return GO_involved_in

    @staticmethod
    def fields():
        return []


class gene_to_molecular_function(ontoweaver.Edge):
    @staticmethod
    def source_type():
        return DB_Object_Symbol

    @staticmethod
    def target_type():
        return GO_enables

    @staticmethod
    def fields():
        return []

# Allow accessing all ontoweaver.Item classes defined in this module.
all = ontoweaver.All(sys.modules[__name__])
