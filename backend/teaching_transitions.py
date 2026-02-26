# teaching_transitions.py

TRANSITION_SENTENCES = {
    ("symbol", "quantifier"): "你刚才的疑惑，其实已经不只是符号本身的问题了，我们需要看看这些符号在“对谁成立”。",

    ("quantifier", "dependency"): "到这里，其实你已经理解了量词本身，现在真正关键的是：它们之间是如何互相制约的。",

    ("dependency", "proof_logic"): "我们现在遇到的，已经不是概念问题，而是整个论证结构该如何运作的问题了。",
}


def get_transition_sentence(old_type: str, new_type: str) -> str | None:
    return TRANSITION_SENTENCES.get((old_type, new_type))

def get_downgrade_sentence(old, new):
    return {
        ("quantifier", "symbol"):
            "我们先别急着讨论量词，我感觉符号本身还可以再稳一下。",
        ("dependency", "quantifier"):
            "在继续依赖关系之前，我们先把“谁先选、谁后选”这一步走扎实。",
        ("proof_logic", "dependency"):
            "证明逻辑有点早了，我们先回到变量之间是怎么被约束的。",
    }.get((old, new), "我们稍微退一步，用更基础的角度重新看一下。")
