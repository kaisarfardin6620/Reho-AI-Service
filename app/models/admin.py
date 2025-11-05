from pydantic import BaseModel, Field
from datetime import datetime
from typing import List
from app.models.feedback import OptimizationInsight 

class AdminAlert(BaseModel):
    user_id: str = Field(..., alias="userId")
    user_email: str = Field(..., alias="userEmail")
    alert_message: str = Field(..., alias="alertMessage")
    category: str  
    created_at: datetime = Field(..., alias="createdAt")

    class Config:
        populate_by_name = True
        by_alias = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class AdminAlertResponse(BaseModel):
    alerts: List[AdminAlert]
class SpendingHeatmapItem(BaseModel):
    category: str
    spending_level: str = Field(..., alias="spendingLevel", description="High, Medium, or Low")

    class Config: 
        populate_by_name = True
        by_alias = True

class DebtStatusItem(BaseModel):
    name: str
    status: str = Field(..., description="E.g., On Track, Missed Payment, High Risk")

    class Config: 
        populate_by_name = True
        by_alias = True

class AdminUserAIDashboard(BaseModel):
    total_monthly_spending: float = Field(..., alias="totalMonthlySpending")
    top_overspending_categories: List[str] = Field(..., alias="topOverspendingCategories")
    spending_growth_from_last_month: str = Field(..., alias="spendingGrowthFromLastMonth")
    
    spending_heatmap: List[SpendingHeatmapItem] = Field(..., alias="spendingHeatmap")
    
    current_alerts: List[AdminAlert] = Field(..., alias="currentAlerts")
    ai_tips: List[OptimizationInsight] = Field(..., alias="aiTips")

    debt_statuses: List[DebtStatusItem] = Field(..., alias="debtStatuses")
    
    class Config:
        populate_by_name = True
        by_alias = True