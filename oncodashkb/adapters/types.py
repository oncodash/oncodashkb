from typing import TypeAlias
from typing import Optional

from . import base

class Patient(base.Node):


    def __init__(self,
        allowed_fields: list[str],
        id            : Optional[str] = None,
        label         : Optional[str] = "",
        properties    : Optional[dict[str,str]] = {}
    ):
        super().__init__(
            allowed_fields,
            "patient_id", # id
            "patient", # label
            {} # properties
        )

