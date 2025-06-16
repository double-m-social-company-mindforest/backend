from pydantic import BaseModel
from typing import List, Optional, Dict, Any


class StrengthWeakness(BaseModel):
    title: str
    description: str


class CharacterType(BaseModel):
    id: int
    name: str
    animal: Optional[str] = None
    group_name: Optional[str] = None
    one_liner: Optional[str] = None
    overview: Optional[str] = None
    greeting: Optional[str] = None
    hashtags: Optional[List[str]] = None
    strengths: Optional[List[StrengthWeakness]] = None
    weaknesses: Optional[List[StrengthWeakness]] = None
    relationship_style: Optional[str] = None
    behavior_pattern: Optional[str] = None
    image_filename: Optional[str] = None
    image_filename_right: Optional[str] = None
    strength_icons: Optional[List[str]] = None
    weakness_icons: Optional[List[str]] = None


class CharacterTypeResponse(BaseModel):
    character: CharacterType


class AllCharacterTypesResponse(BaseModel):
    characters: List[CharacterType]
    total: int