# teaching_styles.py

TEACHING_STYLES = {
    "explain": "直接解释关键概念，但保持简洁，不展开证明",
    "guide": "通过反问或提示，引导学生自己意识到关键点",
}


def get_style_prompt(style: str) -> str:
    return TEACHING_STYLES.get(style, "")
