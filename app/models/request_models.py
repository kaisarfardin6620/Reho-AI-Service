from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class RenameConversationRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)

class OptimizationRequest(BaseModel):
    user_id: str = Field(..., min_length=24, max_length=24)
    report_type: str = Field(..., pattern="^(expense|budget|debt)$")

class WebSocketAuthRequest(BaseModel):
    token: str = Field(..., min_length=1)
    conversation_id: Optional[str] = Field(None, min_length=24, max_length=24)

class AdminAnalysisRequest(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    user_ids: Optional[List[str]] = Field(None, min_items=1)