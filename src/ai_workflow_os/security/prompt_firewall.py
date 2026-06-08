"""
Prompt注入防御模块

检测和防御Prompt注入攻击，保护系统免受恶意输入侵害。
支持正则匹配检测和LLM语义检测两种方式。
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Awaitable
import re
import logging

# 配置日志记录器
logger = logging.getLogger(__name__)


@dataclass
class InjectionPattern:
    """注入模式定义
    
    Attributes:
        pattern_id: 模式唯一标识
        name: 模式名称
        regex_pattern: 正则表达式模式
        severity: 严重程度（low/medium/high/critical）
        description: 模式描述
    """
    pattern_id: str
    name: str
    regex_pattern: str
    severity: str = "medium"
    description: str = ""


@dataclass
class InjectionMatch:
    """注入匹配结果
    
    Attributes:
        pattern_id: 匹配到的模式ID
        matched_text: 匹配到的文本
        position: 匹配位置（起始索引）
        severity: 严重程度
    """
    pattern_id: str
    matched_text: str
    position: int
    severity: str


@dataclass
class FirewallResult:
    """防火墙扫描结果
    
    Attributes:
        safe: 是否安全
        threats: 检测到的威胁列表
        sanitized_prompt: 清洗后的Prompt
        risk_score: 风险分数（0.0-1.0）
    """
    safe: bool
    threats: list[InjectionMatch] = field(default_factory=list)
    sanitized_prompt: str = ""
    risk_score: float = 0.0


class PromptFirewall:
    """Prompt防火墙
    
    检测和防御Prompt注入攻击，保护系统免受恶意输入侵害。
    
    Attributes:
        patterns: 注入模式列表
        llm_detector: LLM检测器（可选）
    """
    
    def __init__(self, llm_detector: Callable[[str], Awaitable[bool]] | None = None) -> None:
        """初始化Prompt防火墙
        
        Args:
            llm_detector: LLM语义检测器，接收Prompt返回是否为注入
        """
        self.patterns: list[InjectionPattern] = []
        self.llm_detector = llm_detector
        
        # 初始化默认注入模式
        self._init_default_patterns()
        
        logger.info("Prompt防火墙已初始化")
    
    def _init_default_patterns(self) -> None:
        """初始化默认注入检测模式"""
        default_patterns = [
            InjectionPattern(
                pattern_id="injection_001",
                name="系统指令注入",
                regex_pattern=r"(?i)(ignore|disregard|forget)\s+(previous|above|all)\s+(instructions?|prompts?|rules?)",
                severity="critical",
                description="检测试图忽略系统指令的注入攻击"
            ),
            InjectionPattern(
                pattern_id="injection_002",
                name="角色扮演注入",
                regex_pattern=r"(?i)(you\s+are\s+now|act\s+as|pretend\s+to\s+be|roleplay\s+as)",
                severity="high",
                description="检测试图改变AI角色的注入攻击"
            ),
            InjectionPattern(
                pattern_id="injection_003",
                name="指令覆盖注入",
                regex_pattern=r"(?i)(new\s+instructions?|override\s+instructions?|instead\s+of|replace\s+with)",
                severity="critical",
                description="检测试图覆盖原始指令的注入攻击"
            ),
            InjectionPattern(
                pattern_id="injection_004",
                name="代码执行注入",
                regex_pattern=r"(?i)(execute|run|eval|exec)\s*(\(|`|'|\")",
                severity="high",
                description="检测试图执行代码的注入攻击"
            ),
            InjectionPattern(
                pattern_id="injection_005",
                name="分隔符注入",
                regex_pattern=r"(---+|===+|\*\*\*+|END\s+OF\s+(PROMPT|INSTRUCTIONS?|CONTEXT))",
                severity="medium",
                description="检测使用分隔符伪造指令边界的注入攻击"
            ),
            InjectionPattern(
                pattern_id="injection_006",
                name="敏感信息提取",
                regex_pattern=r"(?i)(show|reveal|tell|print|output|display)\s+(me\s+)?(your|the|system)\s+(instructions?|prompts?|rules?|config)",
                severity="high",
                description="检测试图提取系统信息的注入攻击"
            ),
            InjectionPattern(
                pattern_id="injection_007",
                name="DAN注入",
                regex_pattern=r"(?i)(do\s+anything\s+now|DAN\s+mode|jailbreak|unrestricted)",
                severity="critical",
                description="检测DAN类型越狱攻击"
            ),
            InjectionPattern(
                pattern_id="injection_008",
                name="编码混淆",
                regex_pattern=r"(?i)(base64|hex|rot13|encode|decode|cipher)",
                severity="medium",
                description="检测使用编码方式混淆的注入攻击"
            ),
        ]
        
        for pattern in default_patterns:
            self.patterns.append(pattern)
        
        logger.debug(f"已初始化 {len(default_patterns)} 个默认注入检测模式")
    
    async def scan_prompt(self, prompt: str) -> FirewallResult:
        """扫描Prompt安全性
        
        Args:
            prompt: 待扫描的Prompt文本
            
        Returns:
            FirewallResult: 扫描结果
        """
        all_threats: list[InjectionMatch] = []
        
        # 正则匹配检测
        regex_threats = self._check_regex_patterns(prompt)
        all_threats.extend(regex_threats)
        
        # LLM语义检测（如果配置了检测器）
        if self.llm_detector:
            is_injection = await self._check_semantic_injection(prompt)
            if is_injection:
                all_threats.append(InjectionMatch(
                    pattern_id="semantic_001",
                    matched_text="[语义分析检测到潜在注入]",
                    position=0,
                    severity="high"
                ))
        
        # 计算风险分数
        risk_score = self._calculate_risk_score(all_threats)
        
        # 判断是否安全（风险分数低于阈值）
        is_safe = risk_score < 0.5
        
        # 清洗Prompt
        sanitized_prompt = await self.sanitize_prompt(prompt) if not is_safe else prompt
        
        result = FirewallResult(
            safe=is_safe,
            threats=all_threats,
            sanitized_prompt=sanitized_prompt,
            risk_score=risk_score
        )
        
        if not is_safe:
            logger.warning(
                f"检测到Prompt注入风险，风险分数: {risk_score:.2f}，"
                f"威胁数量: {len(all_threats)}"
            )
        
        return result
    
    async def sanitize_prompt(self, prompt: str) -> str:
        """清洗Prompt，移除危险内容
        
        Args:
            prompt: 原始Prompt文本
            
        Returns:
            str: 清洗后的安全Prompt
        """
        sanitized = prompt
        
        # 移除检测到的注入内容
        for pattern in self.patterns:
            try:
                compiled_pattern = re.compile(pattern.regex_pattern, re.IGNORECASE)
                sanitized = compiled_pattern.sub("[内容已移除]", sanitized)
            except re.error:
                continue
        
        # 脱敏处理
        sanitized = self._redact_sensitive_info(sanitized)
        
        return sanitized
    
    def add_pattern(self, pattern: InjectionPattern) -> None:
        """添加检测模式
        
        Args:
            pattern: 注入模式定义
        """
        # 检查模式ID是否已存在
        existing = next(
            (p for p in self.patterns if p.pattern_id == pattern.pattern_id),
            None
        )
        
        if existing:
            self.patterns.remove(existing)
            logger.info(f"更新注入检测模式: {pattern.pattern_id} ({pattern.name})")
        
        self.patterns.append(pattern)
        logger.info(f"已添加注入检测模式: {pattern.pattern_id} ({pattern.name})")
    
    def remove_pattern(self, pattern_id: str) -> bool:
        """移除检测模式
        
        Args:
            pattern_id: 模式ID
            
        Returns:
            bool: 移除成功返回True，模式不存在返回False
        """
        pattern = next(
            (p for p in self.patterns if p.pattern_id == pattern_id),
            None
        )
        
        if not pattern:
            logger.warning(f"注入检测模式 '{pattern_id}' 不存在")
            return False
        
        self.patterns.remove(pattern)
        logger.info(f"已移除注入检测模式: {pattern_id} ({pattern.name})")
        return True
    
    def _check_regex_patterns(self, prompt: str) -> list[InjectionMatch]:
        """正则匹配检测
        
        Args:
            prompt: 待检测的Prompt文本
            
        Returns:
            list: 匹配到的注入威胁列表
        """
        threats: list[InjectionMatch] = []
        
        for pattern in self.patterns:
            try:
                compiled_pattern = re.compile(pattern.regex_pattern, re.IGNORECASE)
                matches = compiled_pattern.finditer(prompt)
                
                for match in matches:
                    threats.append(InjectionMatch(
                        pattern_id=pattern.pattern_id,
                        matched_text=match.group(),
                        position=match.start(),
                        severity=pattern.severity
                    ))
            except re.error as e:
                logger.error(f"正则表达式编译失败: {pattern.regex_pattern}, 错误: {str(e)}")
                continue
        
        return threats
    
    async def _check_semantic_injection(self, prompt: str) -> bool:
        """使用LLM检测语义注入
        
        Args:
            prompt: 待检测的Prompt文本
            
        Returns:
            bool: 检测到注入返回True
        """
        if not self.llm_detector:
            return False
        
        try:
            return await self.llm_detector(prompt)
        except Exception as e:
            logger.error(f"LLM语义检测失败: {str(e)}")
            return False
    
    def _redact_sensitive_info(self, prompt: str) -> str:
        """脱敏处理
        
        移除Prompt中的敏感信息，如API密钥、密码等。
        
        Args:
            prompt: 原始Prompt文本
            
        Returns:
            str: 脱敏后的Prompt
        """
        redacted = prompt
        
        # API密钥模式
        api_key_patterns = [
            r"(?i)(api[_-]?key|apikey)\s*[:=]\s*['\"]?[\w\-]+['\"]?",
            r"(?i)(secret|password|passwd|pwd)\s*[:=]\s*['\"]?[\w\-]+['\"]?",
            r"(?i)(token|access_token|auth_token)\s*[:=]\s*['\"]?[\w\-]+['\"]?",
        ]
        
        for api_pattern in api_key_patterns:
            try:
                compiled = re.compile(api_pattern)
                redacted = compiled.sub("[敏感信息已脱敏]", redacted)
            except re.error:
                continue
        
        return redacted
    
    def _calculate_risk_score(self, threats: list[InjectionMatch]) -> float:
        """计算风险分数
        
        Args:
            threats: 检测到的威胁列表
            
        Returns:
            float: 风险分数（0.0-1.0）
        """
        if not threats:
            return 0.0
        
        # 严重程度权重
        severity_weights = {
            "low": 0.1,
            "medium": 0.3,
            "high": 0.6,
            "critical": 1.0
        }
        
        # 计算加权分数
        total_weight = sum(
            severity_weights.get(threat.severity, 0.3)
            for threat in threats
        )
        
        # 限制在0-1范围内
        risk_score = min(total_weight, 1.0)
        
        return risk_score
    
    def get_patterns(self) -> list[dict[str, Any]]:
        """获取所有检测模式
        
        Returns:
            list: 模式信息列表
        """
        return [
            {
                "pattern_id": pattern.pattern_id,
                "name": pattern.name,
                "regex_pattern": pattern.regex_pattern,
                "severity": pattern.severity,
                "description": pattern.description
            }
            for pattern in self.patterns
        ]
    
    def get_statistics(self) -> dict[str, Any]:
        """获取防火墙统计信息
        
        Returns:
            dict: 统计信息
        """
        # 统计各严重程度的模式数量
        severity_counts: dict[str, int] = {}
        for pattern in self.patterns:
            severity_counts[pattern.severity] = severity_counts.get(pattern.severity, 0) + 1
        
        return {
            "total_patterns": len(self.patterns),
            "severity_distribution": severity_counts,
            "llm_detector_enabled": self.llm_detector is not None
        }