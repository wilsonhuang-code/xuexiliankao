# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

with open(r'C:\Users\Administrator\Desktop\学练考\main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the Label part for cards - reduce font_size from 36 and fix variable name
old = '''            lbl_emoji = Label(text=emoji, font_size=36, size_hint=(1, 0.5),
                              color=t["text"], halign="center", valign="bottom")
            lbl_text = Label(text=text, font_size=fs + 2, bold=True, size_hint=(1, 0.5),
                             color=t["text"], halign="center", valign="top")'''

new = '''            lbl_emoji = Label(text=icon_text, font_size=fs+6, bold=True, size_hint=(1, 0.5),
                              color=color, halign="center", valign="bottom")
            lbl_text = Label(text=sub_text, font_size=fs-2, size_hint=(1, 0.5),
                             color=t["text2"], halign="center", valign="top")'''

if old in content:
    content = content.replace(old, new)
    with open(r'C:\Users\Administrator\Desktop\学练考\main.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('OK - replaced')
else:
    print('NOT FOUND')
    # find the exact text around lbl_emoji
    idx = content.find('lbl_emoji = Label')
    if idx >= 0:
        print(repr(content[idx:idx+200]))
