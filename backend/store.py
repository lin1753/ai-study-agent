# store.py

from models import KnowledgeBlockORM, ExplanationBranch

# 数据存储（在内存中，简单示范）
knowledge_blocks = {}
explanation_branches = {}

# 用来存储知识块的简单字典
def add_knowledge_block(kb):
    knowledge_blocks[kb.id] = kb

# 用来存储分支的简单字典
def add_explanation_branch(branch):
    explanation_branches[branch.id] = branch
