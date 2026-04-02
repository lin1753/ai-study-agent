from pydantic import BaseModel

class MasteryUpdate(BaseModel):
    point_id: str
    level: str # 'unknown', 'learning', 'mastered'
