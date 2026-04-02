from pydantic import BaseModel
from typing import Optional

class ChatRequest(BaseModel):
    thread_id: str
    content: str

class MessageResponse(BaseModel):
    role: str
    content: str
    created_at: str

class BranchCreate(BaseModel):
    space_id: str
    source_block_id: Optional[str] = None
    context: Optional[str] = None
    title: Optional[str] = None
