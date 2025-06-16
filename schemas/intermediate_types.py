from pydantic import BaseModel
from typing import List, Optional


class IntermediateType(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    characteristics: Optional[str] = None
    display_order: int


class IntermediateTypesResponse(BaseModel):
    intermediate_types: List[IntermediateType]
    total: int