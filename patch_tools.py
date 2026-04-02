import re

with open('backend/services/upload_agent_tools.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('from backend.agent_controller', 'from agent_controller')

with open('backend/services/upload_agent_tools.py', 'w', encoding='utf-8') as f:
    f.write(text)

