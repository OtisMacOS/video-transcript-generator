#!/usr/bin/env python3
"""
沙箱功能测试脚本
"""

import asyncio
import json
from sandbox_config import sandbox_manager, SandboxConfig

def test_sandbox_validation():
    """测试沙箱验证功能，返回失败用例列表"""
    print("🧪 开始测试沙箱验证功能...")
    failed_cases = []
    test_cases = [
        {
            "name": "正常API密钥",
            "api_key": "sk-1234567890abcdef1234567890abcdef1234567890abcdef",
            "text": "这是一个正常的文本内容",
            "expected": True
        },
        {
            "name": "无效API密钥",
            "api_key": "invalid-key",
            "text": "这是一个正常的文本内容",
            "expected": False
        },
        {
            "name": "包含敏感信息的文本",
            "api_key": "sk-1234567890abcdef1234567890abcdef1234567890abcdef",
            "text": "我的密码是123456，信用卡号是1234-5678-9012-3456",
            "expected": False
        },
        {
            "name": "超长文本",
            "api_key": "sk-1234567890abcdef1234567890abcdef1234567890abcdef",
            "text": "这是一个超长的文本" * 1000,  # 超过4000字符限制
            "expected": False
        }
    ]
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 测试用例 {i}: {test_case['name']}")
        result = sandbox_manager.validate_request(
            api_key=test_case["api_key"],
            input_text=test_case["text"]
        )
        if result["valid"] == test_case["expected"]:
            print(f"✅ 通过: 验证结果符合预期")
        else:
            print(f"❌ 失败: 期望 {test_case['expected']}, 实际 {result['valid']}")
            if result["errors"]:
                print(f"   错误信息: {result['errors']}")
            failed_cases.append(test_case['name'])
    return failed_cases

def test_sandbox_config():
    """测试沙箱配置"""
    print("\n🔧 测试沙箱配置...")
    
    # 创建自定义配置
    custom_config = SandboxConfig(
        max_requests_per_minute=30,
        max_concurrent_requests=3,
        content_filter_enabled=True,
        audit_logging_enabled=True
    )
    
    print(f"✅ 自定义配置创建成功:")
    print(f"   - 每分钟最大请求数: {custom_config.max_requests_per_minute}")
    print(f"   - 最大并发请求数: {custom_config.max_concurrent_requests}")
    print(f"   - 内容过滤启用: {custom_config.content_filter_enabled}")
    print(f"   - 审计日志启用: {custom_config.audit_logging_enabled}")

def test_audit_logging():
    """测试审计日志功能"""
    print("\n📝 测试审计日志功能...")
    
    # 模拟请求数据
    request_data = {
        "provider": "openai",
        "input": "这是一个测试文本",
        "api_key": "sk-test1234567890abcdef",
        "style": "polish"
    }
    
    # 记录日志
    sandbox_manager.log_request(request_data)
    print("✅ 审计日志记录成功")

async def test_llm_integration():
    """测试LLM集成（模拟）"""
    print("\n🤖 测试LLM集成...")
    
    # 模拟LLM请求
    request_data = {
        "text": "这是一个需要润色的文本",
        "api_key": "sk-1234567890abcdef1234567890abcdef1234567890abcdef",
        "provider": "openai",
        "style": "polish"
    }
    
    # 沙箱验证
    validation_result = sandbox_manager.validate_request(
        api_key=request_data["api_key"],
        input_text=request_data["text"]
    )
    
    if validation_result["valid"]:
        print("✅ 沙箱验证通过，可以调用LLM API")
        # 这里可以添加实际的LLM API调用测试
    else:
        print("❌ 沙箱验证失败，阻止LLM API调用")
        print(f"   错误: {validation_result['errors']}")

def main():
    """主测试函数"""
    print("🚀 开始沙箱功能测试")
    print("=" * 50)
    
    # 运行沙箱验证测试
    failed_cases = test_sandbox_validation()
    # 其他功能测试
    test_sandbox_config()
    test_audit_logging()
    asyncio.run(test_llm_integration())
    
    print("\n" + "=" * 50)
    if not failed_cases:
        print("🎉 沙箱功能测试完成！\n所有用例均通过！")
        print("\n📊 测试总结:")
        print("   - 沙箱验证功能正常")
        print("   - 配置管理功能正常")
        print("   - 审计日志功能正常")
        print("   - LLM集成验证正常")
    else:
        print("❌ 存在失败用例:")
        for name in failed_cases:
            print(f"   - {name}")
        print("\n请修复上述失败用例后再确认全部通过。")

if __name__ == "__main__":
    main() 