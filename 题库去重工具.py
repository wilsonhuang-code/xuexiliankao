# -*- coding: utf-8 -*-
"""
题库去重工具
功能: 检查并移除题库中的重复题目
"""

import json
import os

def load_questions():
    """加载题目数据"""
    file_path = r"C:\Users\Administrator\Desktop\学练考\初中信息技术学业水平考试训练系统.py"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 提取选择题题库
    import re
    
    # 查找选择题题库
    choice_match = re.search(r'choice_questions\s*=\s*\[(.*?)\]', content, re.DOTALL)
    if choice_match:
        choice_str = '[' + choice_match.group(1) + ']'
        try:
            choice_questions = eval(choice_str)
        except:
            print("无法解析选择题题库")
            choice_questions = []
    else:
        choice_questions = []
    
    # 查找判断题题库
    tf_match = re.search(r'true_false_questions\s*=\s*\[(.*?)\]', content, re.DOTALL)
    if tf_match:
        tf_str = '[' + tf_match.group(1) + ']'
        try:
            true_false_questions = eval(tf_str)
        except:
            print("无法解析判断题题库")
            true_false_questions = []
    else:
        true_false_questions = []
    
    return choice_questions, true_false_questions

def check_duplicates(questions, q_type):
    """检查重复题目"""
    seen = {}
    duplicates = []
    
    for idx, q in enumerate(questions):
        text = q.get('text', '')
        if text in seen:
            duplicates.append({
                'id': q.get('id'),
                'duplicate_of_id': seen[text],
                'text': text[:50] + '...' if len(text) > 50 else text
            })
        else:
            seen[text] = q.get('id')
    
    return duplicates

def main():
    print("=" * 60)
    print("题库去重工具")
    print("=" * 60)
    print()
    
    print("正在加载题库...")
    choice_questions, true_false_questions = load_questions()
    
    print(f"选择题总数: {len(choice_questions)}")
    print(f"判断题总数: {len(true_false_questions)}")
    print()
    
    # 检查选择题重复
    print("检查选择题重复...")
    choice_dups = check_duplicates(choice_questions, "选择题")
    if choice_dups:
        print(f"  发现 {len(choice_dups)} 道重复题目:")
        for dup in choice_dups[:10]:  # 只显示前10个
            print(f"    ID {dup['id']} 与 ID {dup['duplicate_of_id']} 重复")
            print(f"      题目: {dup['text']}")
        if len(choice_dups) > 10:
            print(f"    ... 还有 {len(choice_dups) - 10} 道重复题目")
    else:
        print("  ✅ 无重复题目")
    
    print()
    
    # 检查判断题重复
    print("检查判断题重复...")
    tf_dups = check_duplicates(true_false_questions, "判断题")
    if tf_dups:
        print(f"  发现 {len(tf_dups)} 道重复题目:")
        for dup in tf_dups[:10]:
            print(f"    ID {dup['id']} 与 ID {dup['duplicate_of_id']} 重复")
            print(f"      题目: {dup['text']}")
        if len(tf_dups) > 10:
            print(f"    ... 还有 {len(tf_dups) - 10} 道重复题目")
    else:
        print("  ✅ 无重复题目")
    
    print()
    print("=" * 60)
    print("检查完成")
    print("=" * 60)
    
    # 保存重复题目报告
    if choice_dups or tf_dups:
        report = {
            "选择题重复": choice_dups,
            "判断题重复": tf_dups
        }
        report_path = r"C:\Users\Administrator\Desktop\学练考\重复题目报告.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"\n重复题目详细报告已保存到: {report_path}")

if __name__ == "__main__":
    main()
