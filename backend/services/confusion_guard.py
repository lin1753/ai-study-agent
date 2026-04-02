# confusion_guard.py

CONFUSION_ORDER = [
    "symbol",
    "quantifier",
    "dependency",
    "proof_logic",
]

def allowed_confusion_types(current_type: str):
    """
    返回当前轮允许使用的 confusion_type
    """
    if current_type not in CONFUSION_ORDER:
        return [current_type]

    idx = CONFUSION_ORDER.index(current_type)
    # 允许当前层级 + 下一层
    return CONFUSION_ORDER[: idx + 2]
