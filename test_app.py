#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速测试脚本 - 验证核心功能
不需要GUI，直接测试逻辑
"""

import sys
import os

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 50)
print("自适应学练考系统 - 功能测试")
print("=" * 50)

# 测试1：导入主程序
print("\n【测试1】导入主程序...")
try:
    import main
    print("✅ 主程序导入成功")
except Exception as e:
    print(f"❌ 主程序导入失败: {e}")
    sys.exit(1)

# 测试2：验证题库数据
print("\n【测试2】验证题库数据...")
try:
    from main import MATH_QUESTIONS, PHYSICS_QUESTIONS, ENGLISH_QUESTIONS, ALL_QUESTIONS
    
    math_count = len(MATH_QUESTIONS)
    physics_count = len(PHYSICS_QUESTIONS)
    english_count = len(ENGLISH_QUESTIONS)
    
    print(f"✅ 数学题库: {math_count} 题")
    print(f"✅ 物理题库: {physics_count} 题")
    print(f"✅ 英语题库: {english_count} 题")
    print(f"✅ 总题库: {math_count + physics_count + english_count} 题")
    
    # 验证题目结构
    sample = MATH_QUESTIONS[0]
    assert "text" in sample, "题目缺少text字段"
    assert "answer" in sample, "题目缺少answer字段"
    assert "explain" in sample, "题目缺少explain字段"
    assert "level" in sample, "题目缺少level字段"
    print("✅ 题目数据结构验证通过")
    
except Exception as e:
    print(f"❌ 题库验证失败: {e}")
    sys.exit(1)

# 测试3：测试自适应训练引擎
print("\n【测试3】测试自适应训练引擎...")
try:
    from main import AdaptiveTrainer
    
    # 创建训练器
    trainer = AdaptiveTrainer("math", MATH_QUESTIONS)
    print(f"✅ 训练器创建成功")
    print(f"   初始难度: {trainer.level} 星")
    print(f"   需要连续正确: {trainer.need_correct} 题")
    
    # 测试获取题目
    result = trainer.next()
    assert result[0] == "question", "获取题目失败"
    print(f"✅ 题目获取成功: {result[1]['text'][:20]}...")
    
    # 测试答案检查（模拟答对）
    trainer.current = (0, MATH_QUESTIONS[0])
    correct, q = trainer.check("∩")
    assert correct == True, "答案检查失败"
    print(f"✅ 答案检查成功 (正确)")
    
    # 测试答案检查（模拟答错）
    trainer.current = (1, MATH_QUESTIONS[1])
    correct, q = trainer.check("错误答案")
    assert correct == False, "答案检查失败"
    print(f"✅ 答案检查成功 (错误)")
    
    print(f"   已掌握题目数: {len(trainer.mastered)}")
    
except Exception as e:
    print(f"❌ 训练引擎测试失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 测试4：测试奖励系统
print("\n【测试4】测试奖励系统...")
try:
    from main import RewardSystem
    
    reward = RewardSystem()
    print(f"✅ 奖励系统创建成功")
    print(f"   初始状态: {reward.get_status()}")
    
    # 测试添加积分
    reward.add_points(10)
    assert reward.points == 10, "积分添加失败"
    print(f"✅ 积分添加成功: {reward.get_status()}")
    
    # 测试添加星星
    reward.add_star()
    assert reward.stars == 1, "星星添加失败"
    print(f"✅ 星星添加成功: {reward.get_status()}")
    
    # 测试3星换1心
    reward.add_star()
    reward.add_star()
    assert reward.stars == 0 and reward.hearts == 1, "星星换心失败"
    print(f"✅ 星星换心成功: {reward.get_status()}")
    
except Exception as e:
    print(f"❌ 奖励系统测试失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 测试5：测试错题本
print("\n【测试5】测试错题本...")
try:
    from main import add_mistake, load_mistakes, MISTAKE_FILE
    
    # 添加测试错题
    add_mistake("math", "测试题目", "错误答案", "正确答案", "讲解")
    print(f"✅ 错题添加成功")
    
    # 加载错题
    mistakes = load_mistakes()
    assert len(mistakes) > 0, "错题加载失败"
    print(f"✅ 错题加载成功: 共 {len(mistakes)} 道")
    print(f"   最新错题: {mistakes[-1]['question']}")
    
except Exception as e:
    print(f"❌ 错题本测试失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 测试6：测试Kivy可用性
print("\n【测试6】测试Kivy可用性...")
try:
    import kivy
    print(f"✅ Kivy版本: {kivy.__version__}")
    
    # 检查必要依赖
    from kivy.app import App
    from kivy.uix.button import Button
    from kivy.uix.label import Label
    from kivy.uix.textinput import TextInput
    print(f"✅ Kivy核心组件导入成功")
    
except Exception as e:
    print(f"❌ Kivy测试失败: {e}")
    print("   请运行: pip install kivy")
    sys.exit(1)

# 总结
print("\n" + "=" * 50)
print("✅ 所有测试通过！")
print("=" * 50)
print("\n核心功能验证:")
print("  ✅ 题库数据完整")
print("  ✅ 自适应训练引擎正常")
print("  ✅ 奖励系统正常")
print("  ✅ 错题本功能正常")
print("  ✅ Kivy环境正常")
print("\n建议下一步:")
print("  1. 运行 python main.py 测试GUI")
print("  2. 在手机上打包测试")
print("  3. 完善英语专项和学习计划功能")
print("=" * 50)
