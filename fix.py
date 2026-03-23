import os
def update_llm_service():
    with open('backend/llm_service.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    content = content.replace("推断的一道例题题干", "必须100%来自原文的例题题干（如果没有这页则返回空）")
    content = content.replace("简单解析（若无则不写）", "严格使用原文解答")
    
    with open('backend/llm_service.py', 'w', encoding='utf-8') as f:
        f.write(content)

update_llm_service()
print('Fix Complete')
