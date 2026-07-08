import logging 
import ontoweaver
from ontoweaver import types as owtypes

class escat_tier_transformer(ontoweaver.base.Transformer):

    def is_type_of_cancer_in(type, list_of_types):
        for t in list_of_types:
            if t in type:
                return True
        return False

    # def description_contains_drugs(descr, list_of_drugs):
    #     for d in list_of_drugs:
    #         if d in descr:
    #             return True
    #     return False
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
#        self.declare = ontoweaver.base.Declare(raise_errors = kwargs["raise_errors"])
        self.declare_types.make_node_class("alteration")
        self.declare_types.make_node_class("treatment")
        self.declare_types.make_edge_class("biomarker_for_treatment_level_IA", getattr(owtypes, "alteration"), getattr(owtypes, "treatment"))
        self.declare_types.make_edge_class("biomarker_for_treatment_level_IC", getattr(owtypes, "alteration"), getattr(owtypes, "treatment"))
        self.declare_types.make_edge_class("biomarker_for_treatment_level_II", getattr(owtypes, "alteration"), getattr(owtypes, "treatment"))
        self.declare_types.make_edge_class("biomarker_for_treatment_level_IIIA", getattr(owtypes, "alteration"), getattr(owtypes, "treatment"))
        self.declare_types.make_edge_class("biomarker_for_treatment_level_IIIB", getattr(owtypes, "alteration"), getattr(owtypes, "treatment"))
        self.declare_types.make_edge_class("biomarker_for_treatment_level_IVA", getattr(owtypes, "alteration"), getattr(owtypes, "treatment"))
        self.declare_types.make_edge_class("biomarker_for_treatment_level_IVB", getattr(owtypes, "alteration"), getattr(owtypes, "treatment"))

    def __call__(self, row, i):
        treatment = str(row["treatment"])
        fda_level = str(row["level_of_evidence"])
        cancer_type = str(row["tumorType"])

        approved_drugs = ["Zenocutuzumab", "Selitrectinib"]
        # approved = description_contains_drugs(str(row["decription"], approved_drugs) and fda_level in ["1", "2"]
        approved = treatment in approved_drugs and fda_level in ["1", "2"]

        # Tier IA
        if fda_level in ["LEVEL_1", "LEVEL_2"] and cancer_type in ["Ovarian", "ovarian"]:
            tier = "IA"
            
        # Tier IC
        elif fda_level in ["LEVEL_1", "LEVEL_2"] and cancer_type in ["Solid", "solid"]:
            tier = "IC"
            
        # Tier II:
        elif fda_level in ["LEVEL_3A"] and \
             cancer_type in ["Solid", "solid", "Ovarian", "ovarian"] and \
             not row["treatment"].contains("Trastuzumab Deruxtecan") and  \
             approved:
            tier = "II"
            
        # Tier IVA
        elif fda_level in ["LEVEL_3A"] and \
             not "Trastuzumab Deruxtecan" in treatment and  \
             cancer_type in ["Ovarian", "ovarian", "Solid", "solid"]:
            tier = "IVA"
        
        # Tier IIIA
        # FIXME NB rule => fda 1 ou 2 mais code de Taru = fda 1, 2 ou 3 et approved a verifier
        elif fda_level in ["LEVEL_1", "LEVEL_2", "LEVEL_3A"] and \
             approved :
             # and cancer_type not in ["ovarian", "ovarian", "Solid", "solid"]
            tier = "IIIA"
            
        # FIXME Tier IIIB ne concerne pas oncokb, donc pas applicable dans le transformer.
        
        # FIXME Tier IVA deuxieme regle a verifier: est-ce qu'on prend que level 4 ou R1 et R2 aussi ?
        elif fda_level in ["LEVEL_4"]:
            tier = "IVA"
            
        # Tier IVB
        else:
            tier = "IVB"
            
        yield treatment, getattr(owtypes, "biomarker_for_treatment_level_"+tier),  getattr(owtypes, "treatment"), None
        
