"""
沙箱配置文件
定义LLM API调用的安全策略和资源限制
"""

import os
from typing import Dict, List, Any
from dataclasses import dataclass
import re

@dataclass
class SandboxConfig:
    """沙箱配置类"""
    
    # 网络访问限制
    allowed_domains: List[str] = None
    max_requests_per_minute: int = 60
    max_concurrent_requests: int = 5
    
    # 资源限制
    max_memory_mb: int = 512
    max_cpu_percent: int = 50
    max_execution_time_seconds: int = 30
    
    # API密钥安全
    api_key_storage_method: str = "environment"  # environment, encrypted_file, proxy
    encryption_enabled: bool = True
    
    # 内容过滤
    content_filter_enabled: bool = True
    blocked_keywords: List[str] = None
    max_input_length: int = 4000
    max_output_length: int = 2000
    
    # 审计日志
    audit_logging_enabled: bool = True
    log_all_requests: bool = True
    log_sensitive_data: bool = False
    
    def __post_init__(self):
        if self.allowed_domains is None:
            self.allowed_domains = [
                "api.openai.com",
                "api.anthropic.com", 
                "api.google.com"
            ]
        
        if self.blocked_keywords is None:
            self.blocked_keywords = [
                "password", "secret", "key", "token",
                "credit card", "ssn", "身份证",
                "密码", "信用卡号", "银行卡号", "账号", "账户"
            ]

class SandboxManager:
    """沙箱管理器"""
    
    def __init__(self, config: SandboxConfig):
        self.config = config
        self.request_count = 0
        self.active_requests = 0
        
    def validate_request(self, api_key: str, input_text: str) -> Dict[str, Any]:
        """验证请求是否安全"""
        errors = []
        
        # 检查API密钥格式
        if not self._validate_api_key(api_key):
            errors.append("无效的API密钥格式")
        
        # 检查输入内容
        if not self._validate_input_content(input_text):
            errors.append("输入内容包含敏感信息")
        
        # 检查资源限制
        if not self._check_resource_limits():
            errors.append("超出资源限制")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    
    def _validate_api_key(self, api_key: str) -> bool:
        """验证API密钥格式"""
        if not api_key or len(api_key) < 20:
            return False
        
        # 检查是否包含敏感信息
        sensitive_patterns = ["sk-", "pk_", "Bearer"]
        return any(pattern in api_key for pattern in sensitive_patterns)
    
    def _validate_input_content(self, text: str) -> bool:
        """验证输入内容安全性"""
        if not self.config.content_filter_enabled:
            return True
        
        # 检查长度
        if len(text) > self.config.max_input_length:
            return False
        
        # 预处理：去除空格和常见标点
        text_clean = re.sub(r"[\s\-，。,.、:：;；_~!@#$%^&*()\[\]{}|\\'\"<>?/]+", "", text.lower())
        # 检查敏感关键词（支持中英文、数字混合，忽略大小写和空格）
        for keyword in self.config.blocked_keywords:
            keyword_clean = re.sub(r"[\s\-，。,.、:：;；_~!@#$%^&*()\[\]{}|\\'\"<>?/]+", "", keyword.lower())
            if keyword_clean in text_clean:
                return False
        # 针对常见敏感信息模式（如信用卡号、身份证号等）
        patterns = [
            r"\d{16}",  # 16位数字（信用卡）
            r"\d{15,18}[xX]?",  # 15-18位身份证
            r"\d{3,4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}"  # 信用卡分段
        ]
        for pat in patterns:
            if re.search(pat, text):
                return False
        return True
    
    def _check_resource_limits(self) -> bool:
        """检查资源限制"""
        if self.active_requests >= self.config.max_concurrent_requests:
            return False
        
        # 这里可以添加更复杂的资源检查逻辑
        return True
    
    def log_request(self, request_data: Dict[str, Any]):
        """记录请求日志"""
        if self.config.audit_logging_enabled:
            # 记录请求信息（不包含敏感数据）
            log_entry = {
                "timestamp": "2024-01-01T00:00:00Z",
                "request_id": "req_123",
                "api_provider": request_data.get("provider"),
                "input_length": len(request_data.get("input", "")),
                "status": "success"
            }
            
            if self.config.log_sensitive_data:
                log_entry["api_key_hash"] = self._hash_api_key(request_data.get("api_key", ""))
            
            print(f"沙箱审计日志: {log_entry}")
    
    def _hash_api_key(self, api_key: str) -> str:
        """对API密钥进行哈希处理"""
        import hashlib
        return hashlib.sha256(api_key.encode()).hexdigest()[:16]

# 默认沙箱配置
DEFAULT_SANDBOX_CONFIG = SandboxConfig()

# 创建沙箱管理器实例
sandbox_manager = SandboxManager(DEFAULT_SANDBOX_CONFIG) 