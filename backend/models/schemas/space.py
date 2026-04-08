from pydantic import BaseModel
from typing import List, Optional

class SpaceCreate(BaseModel):
    name: str

class SpaceResponse(BaseModel):
    id: str
    name: str

class SpaceConfigUpdate(BaseModel):
    priority_chapters: Optional[List[str]] = []
    exam_weights: Optional[dict] = {}
    llm_provider: Optional[str] = "local"
    llm_api_key: Optional[str] = ""
    llm_base_url: Optional[str] = "https://api.deepseek.com/v1"
    llm_model: Optional[str] = "deepseek-chat"
