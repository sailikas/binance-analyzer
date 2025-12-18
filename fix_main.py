import re

with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 修复lambda语法错误
content = re.sub(
    r'lambda x: self\.manager\.current = "(\w+)"',
    r'lambda x: setattr(self.manager, "current", "\1")',
    content
)

# 移除emoji
replacements = {
    '▶ 立即分析': '立即分析',
    '⏰ 定时设置': '定时设置',
    '📜 历史记录': '历史记录',
    '⚙ 设置': '设置',
    '← 返回': '返回',
    '🔄 刷新': '刷新',
    '🔥 ': '#'
}

for old, new in replacements.items():
    content = content.replace(old, new)

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("修复完成")
