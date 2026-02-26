# teaching_goals.py

TEACHING_GOALS = {
    "symbol": [
        "让学生明确当前符号的角色，而不是计算规则",
        "消除学生对符号“人为选择”的直觉误解",
    ],
    "quantifier": [
        "让学生意识到量词是在约束“对谁成立”",
        "让学生区分存在与任意的顺序差异",
    ],
    "dependency": [
        "让学生看清变量之间的先后依赖关系",
        "帮助学生理解选择顺序为何不可交换",
    ],
    "proof_logic": [
        "让学生理解整个论证为何必须这样组织",
        "让学生看到假设—结论结构的必要性",
    ],
}


def get_teaching_goal(confusion_type: str) -> str:
    goals = TEACHING_GOALS.get(confusion_type)
    if not goals:
        return "稳住当前理解，不急于推进"

    # 目前简单选第一个（后面你可以做策略选择）
    return goals[0]
