from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import json
import logging

from core.db import get_db
from models.database import ConversationSpace, MainThread, KnowledgeBlock
from models.schemas.space import SpaceCreate, SpaceResponse, SpaceConfigUpdate
from models.schemas.roadmap import MasteryUpdate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/spaces", tags=["Spaces"])

@router.post("", response_model=SpaceResponse)
def create_space(payload: SpaceCreate, db: Session = Depends(get_db)):
    """创建一个新的科目空间"""
    space = ConversationSpace(name=payload.name)
    db.add(space)
    db.commit()
    db.refresh(space)
    
    # 自动创建主线
    main_thread = MainThread(space_id=space.id)
    db.add(main_thread)
    db.commit()
    
    return SpaceResponse(id=space.id, name=space.name)

@router.get("", response_model=List[SpaceResponse])
def list_spaces(db: Session = Depends(get_db)):
    spaces = db.query(ConversationSpace).all()
    return [SpaceResponse(id=s.id, name=s.name) for s in spaces]

@router.delete("/{space_id}")
def delete_space(space_id: str, db: Session = Depends(get_db)):
    """删除科目空间"""
    space = db.query(ConversationSpace).filter(ConversationSpace.id == space_id).first()
    if not space:
        raise HTTPException(404, "Space not found")
    
    db.delete(space)
    db.commit()
    return {"message": "Space deleted"}

@router.put("/{space_id}")
def update_space(space_id: str, payload: SpaceCreate, db: Session = Depends(get_db)):
    """重命名科目空间"""
    space = db.query(ConversationSpace).filter(ConversationSpace.id == space_id).first()
    if not space:
        raise HTTPException(404, "Space not found")
    
    space.name = payload.name
    db.commit()
    db.refresh(space)
    return SpaceResponse(id=space.id, name=space.name)

@router.put("/{space_id}/config")
def update_space_config(space_id: str, config: SpaceConfigUpdate, db: Session = Depends(get_db)):
    """更新 Space 的考试配置 (V2.0)"""
    space = db.query(ConversationSpace).filter(ConversationSpace.id == space_id).first()
    if not space:
        raise HTTPException(404, "Space not found")
    
    current_config = json.loads(space.config_data or "{}")
    current_config["priority_chapters"] = config.priority_chapters
    current_config["exam_weights"] = config.exam_weights
    current_config["llm_provider"] = config.llm_provider
    current_config["llm_api_key"] = config.llm_api_key
    current_config["llm_base_url"] = config.llm_base_url
    current_config["llm_model"] = config.llm_model
    space.config_data = json.dumps(current_config)
    
    db.commit()
    logger.info(f"Space {space_id} config updated: {current_config}")
    return {"message": "Config updated"}

@router.get("/{space_id}/main_thread")
def get_main_thread_summary(space_id: str, db: Session = Depends(get_db)):
    """获取主线大纲"""
    thread = db.query(MainThread).filter(MainThread.space_id == space_id).first()
    if not thread:
        return {"summary": "", "roadmap": [], "mastery": {}}
    return {
        "id": thread.id,
        "summary": thread.current_summary,
        "roadmap": json.loads(thread.roadmap_json or "[]"),
        "mastery": json.loads(thread.mastery_data or "{}")
    }

@router.put("/{space_id}/mastery")
def update_mastery(space_id: str, payload: MasteryUpdate, db: Session = Depends(get_db)):
    """更新知识点掌握度"""
    thread = db.query(MainThread).filter(MainThread.space_id == space_id).first()
    if not thread:
        raise HTTPException(404, "Main thread not found")
    
    mastery = json.loads(thread.mastery_data or "{}")
    mastery[payload.point_id] = payload.level
    thread.mastery_data = json.dumps(mastery)
    db.commit()
    return {"message": "Mastery updated"}

@router.get("/{space_id}/blocks")
def get_blocks(space_id: str, db: Session = Depends(get_db)):
    blocks = db.query(KnowledgeBlock).filter(KnowledgeBlock.space_id == space_id).all()
    return [{"id": b.id, "text": b.raw_text, "file_id": b.source_file_id} for b in blocks]
