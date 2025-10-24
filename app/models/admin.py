from pydantic import BaseModel, Field
from datetime import datetime
from typing import List

class AdminAlert(BaseModel):
    user_id: str = Field(..., alias="userId")
    user_email: str = Field(..., alias="userEmail")
    alert_message: str = Field(..., alias="alertMessage")
    category: str  
    created_at: datetime = Field(..., alias="createdAt")

    class Config:
        populate_by_name = True

class AdminAlertResponse(BaseModel):
    alerts: List[AdminAlert]