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
        return []

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


class gene_hugo(ontoweaver.Node):
    @staticmethod
    def fields():
        return []

class biological_process(ontoweaver.Node):
    @staticmethod
    def fields():
        return []

class molecular_function(ontoweaver.Node):
    @staticmethod
    def fields():
        return []
class gene_to_biological_process(ontoweaver.Edge):
    @staticmethod
    def source_type():
        return gene_hugo

    @staticmethod
    def target_type():
        return biological_process

    @staticmethod
    def fields():
        return []


class gene_to_molecular_function(ontoweaver.Edge):
    @staticmethod
    def source_type():
        return gene_hugo

    @staticmethod
    def target_type():
        return molecular_function

    @staticmethod
    def fields():
        return []

class evidence(ontoweaver.Node):
    @staticmethod
    def fields():
        return []

class id(ontoweaver.Node):
    @staticmethod
    def fields():
        return []

class disease(ontoweaver.Node):
    @staticmethod
    def fields():
        return []

class drug(ontoweaver.Node):
    @staticmethod
    def fields():
        return []

class target(ontoweaver.Node):
    @staticmethod
    def fields():
        return []

class approvedSymbol(ontoweaver.Node):
    @staticmethod
    def fields():
        return []

class disease_to_drug(ontoweaver.Edge):
    @staticmethod
    def source_type():
        return disease

    @staticmethod
    def target_type():
        return drug

    @staticmethod
    def fields():
        return []

class ensemble_id_to_hugo_symbol(ontoweaver.Edge):
    @staticmethod
    def source_type():
        return target

    @staticmethod
    def target_type():
        return gene_hugo

    @staticmethod
    def fields():
        return []


class drug_to_target(ontoweaver.Edge):
    @staticmethod
    def source_type():
        return drug

    @staticmethod
    def target_type():
        return target

    @staticmethod
    def fields():
        return []


# Allow accessing all ontoweaver.Item classes defined in this module.
all = ontoweaver.All(sys.modules[__name__])
