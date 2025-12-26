from pydantic import BaseModel, Field

class SavingsCalculatorRequest(BaseModel):
    amount: float
    frequency: str = Field(..., description="e.g., Monthly, Yearly")
    return_rate: float = Field(..., alias="returnRate")
    inflation_years: float = Field(..., alias="inflationYears")
    taxation_rate: str = Field(..., alias="taxationRate", description="e.g., 20% BRT")
    
    class Config:
        populate_by_name = True

class CalculatorTipsResponse(BaseModel):
    savings_tip: str = Field(..., alias="savingsTip", description="Tip for Regular Savings screen.")
    loan_tip: str = Field(..., alias="loanTip", description="Tip for Finance Calculator (Loan Repayment).")
    future_value_tip: str = Field(..., alias="futureValueTip", description="Tip for Inflation Calculator (Future Value).")
    historical_tip: str = Field(..., alias="historicalTip", description="Tip for Inflation Calculator (Historical Value).")

    class Config:
        populate_by_name = True