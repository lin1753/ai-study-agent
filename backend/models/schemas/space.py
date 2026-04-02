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
