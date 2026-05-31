#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动测试脚本 - 测试所有功能并生成报告
"""

import sys
import os
import json
from datetime import datetime

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("自适应学练考系统 - 自动测试")
print("=" * 60)

# 测试结果
results = {
    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "tests": []
}

def test(name, func):
    """运行单个测试"""
    print(f"\n[测试] {name}...")
    try:
        result = func()
        if result:
            print(f"✅ {name} - 通过")
            results["tests"].append({"name": name, "status": "pass"})
            return True
        else:
            print(f"❌ {name} - 失败")
            results["tests"].append({"name": name, "status": "fail"})
            return False
    except Exception as e:
        print(f"❌ {name} - 异常: {e}")
        results["tests"].append({"name": name, "status": "error", "error": str(e)})
        return False

# 测试1：导入主程序
def test_import():
    global MATH_QUESTIONS, PHYSICS_QUESTIONS, ENGLISH_QUESTIONS, ALL_QUESTIONS
    global AdaptiveTrainer, RewardSystem, load_mistakes, save_mistakes, add_mistake
    
    import main
    MATH_QUESTIONS = main.MATH_QUESTIONS
    PHYSICS_QUESTIONS = main.PHYSICS_QUESTIONS
    ENGLISH_QUESTIONS = main.ENGLISH_QUESTIONS
    ALL_QUESTIONS = main.ALL_QUESTIONS
    AdaptiveTrainer = main.AdaptiveTrainer
    RewardSystem = main.RewardSystem
    load_mistakes = main.load_mistakes
    save_mistakes = main.save_mistakes
    add_mistake = main.add_mistake
    return True

test("导入主程序", test_import)

# 测试2：验证题库数据
def test_questions():
    assert len(MATH_QUESTIONS) > 0, "数学题库为空"
    assert len(PHYSICS_QUESTIONS) > 0, "物理题库为空"
    assert len(ENGLISH_QUESTIONS) > 0, "英语题库为空"
    
    # 检查题目结构
    for q in MATH_QUESTIONS:
        assert "text" in q, "题目缺少text字段"
        assert "answer" in q, "题目缺少answer字段"
        assert "explain" in q, "题目缺少explain字段"
        assert "level" in q, "题目缺少level字段"
    
    return True

test("验证题库数据", test_questions)

# 测试3：测试自适应训练引擎
def test_trainer():
    trainer = AdaptiveTrainer("math", MATH_QUESTIONS)
    
    # 测试初始状态
    assert trainer.level == 1, "初始难度应为1"
    assert trainer.correct_in_level == 0, "初始连续正确数应为0"
    
    # 测试获取题目
    result = trainer.next()
    assert result[0] == "question", "获取题目失败"
    
    # 测试答案检查（答对）
    trainer.current = (0, MATH_QUESTIONS[0])
    correct, q = trainer.check("∩")
    assert correct == True, "答案检查失败（应正确）"
    assert trainer.correct_in_level == 1, "连续正确数应为1"
    
    # 测试答案检查（答错）
    trainer.correct_in_level = 0  # 重置
    trainer.current = (1, MATH_QUESTIONS[1])
    correct, q = trainer.check("错误答案")
    assert correct == False, "答案检查失败（应错误）"
    assert trainer.correct_in_level == 0, "答错后连续正确数应为0"
    
    return True

test("测试自适应训练引擎", test_trainer)

# 测试4：测试奖励系统
def test_reward():
    reward = RewardSystem()
    initial_points = reward.points
    initial_stars = reward.stars
    initial_hearts = reward.hearts
    
    # 测试添加积分
    reward.add_points(10)
    assert reward.points == initial_points + 10, "积分添加失败"
    
    # 测试添加星星
    reward.add_star()
    assert reward.stars == initial_stars + 1, "星星添加失败"
    
    # 测试3星换1心
    reward.stars = 2
    reward.add_star()
    assert reward.stars == 0, "星星未清零"
    assert reward.hearts == initial_hearts + 1, "爱心添加失败"
    
    return True

test("测试奖励系统", test_reward)

# 测试5：测试错题本
def test_mistakes():
    # 清空错题本（测试用）
    if os.path.exists("mistakes.json"):
        os.remove("mistakes.json")
    
    # 添加错题
    add_mistake("math", "测试题目", "错误答案", "正确答案", "讲解")
    
    # 加载错题
    mistakes = load_mistakes()
    assert len(mistakes) == 1, "错题数量错误"
    assert mistakes[0]["question"] == "测试题目", "错题内容错误"
    
    # 清理
    if os.path.exists("mistakes.json"):
        os.remove("mistakes.json")
    
    return True

test("测试错题本", test_mistakes)

# 测试6：测试Kivy可用性
def test_kivy():
    import kivy
    assert kivy.__version__ >= "2.0.0", "Kivy版本过低"
    
    from kivy.app import App
    from kivy.uix.button import Button
    from kivy.uix.label import Label
    from kivy.uix.textinput import TextInput
    
    return True

test("测试Kivy可用性", test_kivy)

# 生成测试报告
print("\n" + "=" * 60)
print("测试报告")
print("=" * 60)

passed = sum(1 for t in results["tests"] if t["status"] == "pass")
failed = sum(1 for t in results["tests"] if t["status"] == "fail")
errors = sum(1 for t in results["tests"] if t["status"] == "error")

print(f"总计: {len(results['tests'])} 个测试")
print(f"通过: {passed} 个")
print(f"失败: {failed} 个")
print(f"异常: {errors} 个")

if failed == 0 and errors == 0:
    print("\n✅ 所有测试通过！程序可以正常运行。")
    print("\n建议下一步:")
    print("  1. 运行 python main.py 测试GUI")
    print("  2. 在手机上打包测试")
else:
    print("\n❌ 存在测试失败，请检查错误信息。")

# 保存测试报告
with open("test_report.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f"\n测试报告已保存到: test_report.json")
print("=" * 60)
