TEACHING_STRATEGIES = {
    "symbol": [
        "使用生活化类比",
        "强调直觉而不是形式",
        "允许不精确但清楚的说法",
    ],
    "quantifier": [
        "强调先后顺序",
        "用对抗/博弈视角",
        "反复使用“你先选 / 我再选”",
    ],
    "dependency": [
        "明确变量之间的因果链",
        "强调“依赖于什么，而不依赖什么”",
        "使用 if-then 结构",
    ],
    "proof_logic": [
        "解释为什么不能反过来",
        "指出常见错误证明",
        "从失败的尝试入手",
    ],
}


def get_teaching_strategy(confusion_type: str) -> list[str]:
    return TEACHING_STRATEGIES.get(confusion_type, [])
