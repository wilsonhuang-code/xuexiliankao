# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

with open(r'C:\Users\Administrator\Desktop\学练考\main.py', 'r', encoding='utf-8') as f:
    content = f.read()

old = '''        card_configs = [
            ("[练]", "自适应训练", t["primary"], "go_train"),
            ("[英]", "英语专项", t["secondary"], "go_english"),
            ("[考]", "考试模式", "#9C27B0", "go_exam"),
            ("[错]", "错题本", t["error"], "go_mistakes"),
            ("[统]", "学习统计", "#00BCD4", "go_stats"),
            ("[设]", "设置", t["accent"], "go_settings"),
        ]
        for emoji, text, color, method in card_configs:
            card = BGBoxLayout(orientation='vertical', padding=10, radius=16)
            card.set_bg(t["card"])
            lbl_emoji = Label(text=emoji, font_size=36, size_hint=(1, 0.5),
                              color=t["text"], halign="center", valign="bottom")
            lbl_text = Label(text=text, font_size=fs + 2, bold=True, size_hint=(1, 0.5),
                             color=t["text"], halign="center", valign="top")'''

new = '''        card_configs = [
            ("训练", "自适应训练", t["primary"], "go_train"),
            ("英语", "英语专项", t["secondary"], "go_english"),
            ("考试", "考试模式", "#9C27B0", "go_exam"),
            ("错题", "错题本", t["error"], "go_mistakes"),
            ("统计", "学习统计", "#00BCD4", "go_stats"),
            ("设置", "设置", t["accent"], "go_settings"),
        ]
        for icon_text, sub_text, color, method in card_configs:
            card = BGBoxLayout(orientation='vertical', padding=10, radius=16)
            card.set_bg(t["card"])
            lbl_emoji = Label(text=icon_text, font_size=fs+6, bold=True, size_hint=(1, 0.5),
                              color=color, halign="center", valign="bottom")
            lbl_text = Label(text=sub_text, font_size=fs-2, size_hint=(1, 0.5),
                             color=t["text2"], halign="center", valign="top")'''

if old in content:
    content = content.replace(old, new)
    with open(r'C:\Users\Administrator\Desktop\学练考\main.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('OK - replaced')
else:
    print('NOT FOUND - searching...')
    idx = content.find('card_configs')
    if idx >= 0:
        print(repr(content[idx:idx+600]))
