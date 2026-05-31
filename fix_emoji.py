import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
with open(r'C:\Users\Administrator\Desktop\学练考\main.py', 'r', encoding='utf-8') as f:
    content = f.read()

replacements = {
    '\u2605': '[*]', '\U0001f31f': '[*]', '\U0001f3c5': '[OK]',
    '\U0001f393': '[毕]', '\U0001f4c6': '[日]', '\U0001f5d3': '[历]',
    '\U0001f530': '[新]', '\U0001f451': '[王]', '\u26a1': '[!]',
    '\U0001f32a': '[风]', '\U0001f48e': '[钻]', '\u2764': '[心]',
    '\ufe0f': '',
    '\u269b': '[物]', '\u26a0': '[!]', '\U0001f3a5': '[影]',
    '\U0001f500': '[混]', '\u2717': '[X]', '\u2713': '[V]',
    '\U0001f550': '[时]',
}

count = 0
for emoji, text in replacements.items():
    new_content = content.replace(emoji, text)
    if new_content != content:
        c = content.count(emoji)
        count += c
        print(f'  U+{ord(emoji):04X} -> {text} ({c} times)', flush=True)
    content = new_content

content = content.replace("[\u8bcd\u5e93] \u5b66\u7ec3\u8003\u7cfb\u7edf", "\u5b66\u7ec3\u8003\u7cfb\u7edf")

with open(r'C:\Users\Administrator\Desktop\学练考\main.py', 'w', encoding='utf-8') as f:
    f.write(content)
print(f'\nTotal: {count}', flush=True)

remaining = []
for ch in content:
    code = ord(ch)
    if (0x1F000 <= code <= 0xFFFF or 0x2600 <= code <= 0x27BF):
        if ch not in remaining:
            remaining.append(ch)
if remaining:
    print(f'Warning: still has: {remaining}')
else:
    print('All emoji cleared!')
