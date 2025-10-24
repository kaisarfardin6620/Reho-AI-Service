from pydantic import BaseModel, Field
from datetime import datetime
from typing import List

class Suggestion(BaseModel):
    text: str
    category: str  
    created_at: datetime = Field(..., alias="createdAt")

    class Config:
        populate_by_name = True

class SuggestionResponse(BaseModel):
    suggestions: List[Suggestion]