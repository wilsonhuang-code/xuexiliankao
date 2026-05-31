# -*- coding: utf-8 -*-
import re

text = "\u2460____\u2192A____ \u2461____\u2192B____ \u2462____\u2192C____"
print("原文:", text)

pattern = r'([A-Z\u2460-\u2473])(_{2,})'
matches = list(re.finditer(pattern, text))
print(f"\u5339\u914d\u5230 {len(matches)} \u4e2a\u7a7a\u767d:")
for i, m in enumerate(matches):
    print(f"  {i+1}. {m.group()} at pos {m.start()}-{m.end()}")

answers = ["\u751f\u957f\u70b9,\u9876\u82bd", "\u5e7c\u53f6,\u53f6", "\u82bd\u539f\u57fa,\u4fa7\u82bd"]
expanded = []
for a in answers:
    s = str(a).strip()
    if ',' in s and '\uff0c' not in s:
        parts = [p.strip() for p in s.split(',')]
        expanded.extend(parts)
    elif '\uff0c' in s:
        parts = [p.strip() for p in s.split('\uff0c')]
        expanded.extend(parts)
    else:
        expanded.append(s)
print(f"\u5c55\u5f00\u540e\u7b54\u6848: {expanded}")
print(f"\u5339\u914d\u6570={len(matches)}, \u7b54\u6848\u6570={len(expanded)}")

result = text
offset = 0
for match, ans in zip(matches, expanded):
    start = match.start() + offset
    end = match.end() + offset
    marker = match.group(1)
    replacement = marker + '__' + ans + '__'
    result = result[:start] + replacement + result[end:]
    offset += len(replacement) - (end - start)
print(f"\u7ed3\u679c: {result}")
