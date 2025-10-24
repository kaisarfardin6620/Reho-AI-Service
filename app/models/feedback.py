from pydantic import BaseModel, Field
from typing import List

class OptimizationInsight(BaseModel):
    insight: str = Field(..., description="The specific piece of advice or observation.")
    suggestion: str = Field(..., description="A concrete action the user can take.")
    category: str = Field(..., description="The financial area this insight pertains to, e.g., 'Spending', 'Subscriptions'.")

class OptimizationResponse(BaseModel):
    summary: str = Field(..., description="A high-level summary of the AI's findings.")
    insights: List[OptimizationInsight]