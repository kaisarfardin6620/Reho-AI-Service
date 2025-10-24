from pydantic import BaseModel, Field
from datetime import datetime

class ConversationInfo(BaseModel):
    conversation_id: str
    title: str
    created_at: datetime = Field(..., alias="createdAt")

    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class RenameConversationRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=100, description="The new title for the conversation.")