import re

with open('backend/services/upload_service.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Fix literal newline in string
text = text.replace('full_text_for_summary += text + "\\n"', 'full_text_for_summary += text + "\\n"')
text = re.sub(r'full_text_for_summary \+= text \+ "\n"', 'full_text_for_summary += text + "\\n"', text)

with open('backend/services/upload_service.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("Fixed newline characters")
