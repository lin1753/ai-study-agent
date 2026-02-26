# models.py
import uuid
import enum
from datetime import datetime
from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Boolean, Enum
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from db import Base

def generate_uuid():
    return uuid.uuid4().hex

class ThreadStatus(str, enum.Enum):
    EXPLORING = "exploring"
    MATURE = "mature"

class RoleType(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class ConversationSpace(Base):
    """
    科目空间 (Subject)
    代表一个独立的复习科目，如 '高等数学'
    """
    __tablename__ = "conversation_spaces"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    config_data = Column(Text, default="{}")  # Stores user configuration (priority chapters, exam weights)

    # Relationships
    files = relationship("FileRecord", back_populates="space", cascade="all, delete-orphan")
    knowledge_blocks = relationship("KnowledgeBlock", back_populates="space", cascade="all, delete-orphan")
    main_thread = relationship("MainThread", uselist=False, back_populates="space", cascade="all, delete-orphan")
    branch_threads = relationship("BranchThread", back_populates="space", cascade="all, delete-orphan")

class FileRecord(Base):
    """
    文件记录
    上传的 PDF/PPT 文件
    """
    __tablename__ = "file_records"

    id = Column(String, primary_key=True, default=generate_uuid)
    space_id = Column(String, ForeignKey("conversation_spaces.id"), nullable=False)
    filename = Column(String, nullable=False)
    filepath = Column(String, nullable=False)
    file_type = Column(String, nullable=False) # 'pdf', 'ppt'
    processed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    space = relationship("ConversationSpace", back_populates="files")
    blocks = relationship("KnowledgeBlock", back_populates="source_file")

class KnowledgeBlock(Base):
    """
    知识块 (Core Unit)
    从文件解析出的最小知识单元 (一段话或一页PPT)
    """
    __tablename__ = "knowledge_blocks"

    id = Column(String, primary_key=True, default=generate_uuid)
    space_id = Column(String, ForeignKey("conversation_spaces.id"), nullable=False)
    source_file_id = Column(String, ForeignKey("file_records.id"), nullable=False)
    
    raw_text = Column(Text, nullable=False)
    chunk_index = Column(String, nullable=True) # 用于排序或定位
    embedding = Column(Vector(768), nullable=True) # nomic-embed-text 输出为 768 维向量

    space = relationship("ConversationSpace", back_populates="knowledge_blocks")
    source_file = relationship("FileRecord", back_populates="blocks")
    branches = relationship("BranchThread", back_populates="source_block")

class MainThread(Base):
    """
    主线认知 (Main Thread)
    科目的主线总结
    """
    __tablename__ = "main_threads"

    id = Column(String, primary_key=True, default=generate_uuid)
    space_id = Column(String, ForeignKey("conversation_spaces.id"), nullable=False)
    current_summary = Column(Text, default="")
    roadmap_json = Column(Text, default="[]") # Structured cards
    mastery_data = Column(Text, default="{}") # {point_id: level}
    updated_at = Column(DateTime, default=datetime.utcnow)

    space = relationship("ConversationSpace", back_populates="main_thread")
    messages = relationship("Message", back_populates="main_thread", cascade="all, delete-orphan")

class BranchThread(Base):
    """
    分支对话 (Branch Thread)
    针对某个知识点的深入探讨
    """
    __tablename__ = "branch_threads"

    id = Column(String, primary_key=True, default=generate_uuid)
    space_id = Column(String, ForeignKey("conversation_spaces.id"), nullable=False)
    source_block_id = Column(String, ForeignKey("knowledge_blocks.id"), nullable=False)
    
    title = Column(String, nullable=True) # 自动生成或前端展示用
    status = Column(Enum(ThreadStatus), default=ThreadStatus.EXPLORING)
    created_at = Column(DateTime, default=datetime.utcnow)

    space = relationship("ConversationSpace", back_populates="branch_threads")
    source_block = relationship("KnowledgeBlock", back_populates="branches")
    messages = relationship("Message", back_populates="branch_thread", cascade="all, delete-orphan")

class Message(Base):
    """
    通用消息模型
    """
    __tablename__ = "messages"

    id = Column(String, primary_key=True, default=generate_uuid)
    # 消息可能属于主线，也可能属于分支。
    # 这里我们用两个 FK，或者用一个 generic FK。为了利用 SQL FK 约束，使用两个 nullable FK。
    main_thread_id = Column(String, ForeignKey("main_threads.id"), nullable=True)
    branch_thread_id = Column(String, ForeignKey("branch_threads.id"), nullable=True)
    
    role = Column(Enum(RoleType), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    main_thread = relationship("MainThread", back_populates="messages")
    branch_thread = relationship("BranchThread", back_populates="messages")
