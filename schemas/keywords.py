from pydantic import BaseModel
from typing import List


class KeywordItem(BaseModel):
    id: int
    name: str
    main_keyword: str


class CategoryKeywords(BaseModel):
    id: int
    name: str
    english_name: str
    description: str
    instruction: str
    keywords: List[KeywordItem]


class CategoryResponse(BaseModel):
    category: CategoryKeywords


class AllCategoriesResponse(BaseModel):
    categories: List[CategoryKeywords]