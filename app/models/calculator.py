from pydantic import BaseModel, Field

class SavingsCalculatorRequest(BaseModel):
    amount: float
    frequency: str = Field(..., description="e.g., Monthly, Yearly")
    return_rate: float = Field(..., alias="returnRate")
    inflation_years: float = Field(..., alias="inflationYears")
    taxation_rate: str = Field(..., alias="taxationRate", description="e.g., 20% BRT")
    
    class Config:
        populate_by_name = True

class FinancialTipResponse(BaseModel):
    tip: str = Field(..., description="The single, AI-generated financial tip.")