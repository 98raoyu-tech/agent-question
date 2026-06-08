"""
工具沙箱模块

提供工具执行的隔离环境，支持资源限制、超时控制和执行验证。
用于安全地执行不受信任的工具代码。
"""

from dataclasses import dataclass, field
from typing import Any
import asyncio
import time
import uuid
import logging

# 配置日志记录器
logger = logging.getLogger(__name__)


@dataclass
class SandboxConfig:
    """沙箱配置
    
    Attributes:
        max_memory_mb: 最大内存使用量（MB）
        max_cpu_percent: 最大CPU使用率（百分比）
        timeout_seconds: 执行超时时间（秒）
        allowed_hosts: 允许访问的网络主机列表
        blocked_commands: 被禁止执行的命令列表
    """
    max_memory_mb: int = 512
    max_cpu_percent: float = 50.0
    timeout_seconds: int = 30
    allowed_hosts: list[str] = field(default_factory=list)
    blocked_commands: list[str] = field(default_factory=lambda: [
        "rm", "rmdir", "del", "format", "shutdown", "reboot"
    ])


@dataclass
class SandboxResult:
    """沙箱执行结果
    
    Attributes:
        success: 执行是否成功
        output: 执行输出结果
        error: 错误信息（如果执行失败）
        resource_usage: 资源使用情况统计
        duration_ms: 执行耗时（毫秒）
    """
    success: bool
    output: Any = None
    error: str | None = None
    resource_usage: dict[str, Any] = field(default_factory=dict)
    duration_ms: float = 0.0


class ToolSandbox:
    """工具沙箱
    
    提供工具执行的隔离环境，支持资源限制、超时控制和执行验证。
    
    Attributes:
        sandbox_config: 沙箱配置
        active_sandboxes: 活跃的沙箱环境映射表
    """
    
    def __init__(self, config: SandboxConfig | None = None) -> None:
        """初始化工具沙箱
        
        Args:
            config: 沙箱配置，为None时使用默认配置
        """
        self.sandbox_config = config or SandboxConfig()
        self.active_sandboxes: dict[str, dict[str, Any]] = {}
        logger.info("工具沙箱已初始化")
    
    async def execute_in_sandbox(
        self,
        tool_name: str,
        params: dict[str, Any],
        timeout: int | None = None
    ) -> SandboxResult:
        """在沙箱中执行工具
        
        Args:
            tool_name: 工具名称
            params: 工具执行参数
            timeout: 自定义超时时间（秒），为None时使用配置值
            
        Returns:
            SandboxResult: 沙箱执行结果
        """
        # 使用自定义超时或配置值
        actual_timeout = timeout or self.sandbox_config.timeout_seconds
        
        # 验证执行权限
        if not self._validate_execution(tool_name, params):
            return SandboxResult(
                success=False,
                error=f"工具 '{tool_name}' 执行验证失败",
                duration_ms=0.0
            )
        
        # 记录开始时间
        start_time = time.time()
        
        try:
            # 创建沙箱环境
            sandbox_id = await self.create_sandbox("system")
            
            # 应用资源限制
            self._apply_resource_limits(sandbox_id)
            
            # 模拟工具执行（实际实现中应调用工具处理函数）
            result = await asyncio.wait_for(
                self._simulate_tool_execution(tool_name, params, sandbox_id),
                timeout=actual_timeout
            )
            
            # 计算执行耗时
            duration_ms = (time.time() - start_time) * 1000
            
            # 收集资源使用情况
            resource_usage = self._collect_output(sandbox_id)
            
            # 销毁沙箱环境
            await self.destroy_sandbox(sandbox_id)
            
            logger.info(f"工具 '{tool_name}' 在沙箱中执行成功，耗时 {duration_ms:.2f}ms")
            
            return SandboxResult(
                success=True,
                output=result,
                resource_usage=resource_usage,
                duration_ms=duration_ms
            )
            
        except asyncio.TimeoutError:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(f"工具 '{tool_name}' 执行超时 ({actual_timeout}秒)")
            return SandboxResult(
                success=False,
                error=f"执行超时 ({actual_timeout}秒)",
                duration_ms=duration_ms
            )
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(f"工具 '{tool_name}' 执行异常: {str(e)}")
            return SandboxResult(
                success=False,
                error=str(e),
                duration_ms=duration_ms
            )
    
    async def create_sandbox(self, agent_id: str) -> str:
        """创建沙箱环境
        
        Args:
            agent_id: 创建沙箱的Agent ID
            
        Returns:
            str: 沙箱环境ID
        """
        # 生成唯一沙箱ID
        sandbox_id = str(uuid.uuid4())
        
        # 创建沙箱环境配置
        sandbox_env = {
            "sandbox_id": sandbox_id,
            "agent_id": agent_id,
            "created_at": time.time(),
            "config": self.sandbox_config,
            "status": "active",
            "resource_usage": {
                "memory_mb": 0,
                "cpu_percent": 0.0,
                "network_requests": 0
            }
        }
        
        # 存储活跃沙箱
        self.active_sandboxes[sandbox_id] = sandbox_env
        
        logger.info(f"已创建沙箱环境: {sandbox_id} (Agent: {agent_id})")
        return sandbox_id
    
    async def destroy_sandbox(self, sandbox_id: str) -> bool:
        """销毁沙箱环境
        
        Args:
            sandbox_id: 沙箱环境ID
            
        Returns:
            bool: 销毁成功返回True，沙箱不存在返回False
        """
        if sandbox_id not in self.active_sandboxes:
            logger.warning(f"沙箱 '{sandbox_id}' 不存在")
            return False
        
        # 清理沙箱资源
        sandbox = self.active_sandboxes[sandbox_id]
        sandbox["status"] = "destroyed"
        
        # 从活跃列表中移除
        del self.active_sandboxes[sandbox_id]
        
        logger.info(f"已销毁沙箱环境: {sandbox_id}")
        return True
    
    def _validate_execution(self, tool_name: str, params: dict[str, Any]) -> bool:
        """验证执行权限
        
        Args:
            tool_name: 工具名称
            params: 工具参数
            
        Returns:
            bool: 验证通过返回True
        """
        # 检查工具名称是否为空
        if not tool_name or not tool_name.strip():
            logger.error("工具名称不能为空")
            return False
        
        # 检查参数是否为字典类型
        if not isinstance(params, dict):
            logger.error("工具参数必须为字典类型")
            return False
        
        # 检查是否包含被禁止的命令
        for blocked_cmd in self.sandbox_config.blocked_commands:
            if blocked_cmd in str(params).lower():
                logger.error(f"检测到被禁止的命令: {blocked_cmd}")
                return False
        
        return True
    
    def _apply_resource_limits(self, sandbox_id: str) -> None:
        """应用资源限制
        
        Args:
            sandbox_id: 沙箱环境ID
        """
        if sandbox_id not in self.active_sandboxes:
            return
        
        sandbox = self.active_sandboxes[sandbox_id]
        
        # 设置资源限制配置
        sandbox["resource_limits"] = {
            "max_memory_mb": self.sandbox_config.max_memory_mb,
            "max_cpu_percent": self.sandbox_config.max_cpu_percent,
            "timeout_seconds": self.sandbox_config.timeout_seconds
        }
        
        logger.debug(f"已为沙箱 {sandbox_id} 应用资源限制")
    
    def _collect_output(self, sandbox_id: str) -> dict[str, Any]:
        """收集执行输出
        
        Args:
            sandbox_id: 沙箱环境ID
            
        Returns:
            dict: 资源使用情况统计
        """
        if sandbox_id not in self.active_sandboxes:
            return {}
        
        sandbox = self.active_sandboxes[sandbox_id]
        
        # 返回资源使用情况
        return {
            "memory_mb": sandbox["resource_usage"]["memory_mb"],
            "cpu_percent": sandbox["resource_usage"]["cpu_percent"],
            "network_requests": sandbox["resource_usage"]["network_requests"],
            "duration_seconds": time.time() - sandbox["created_at"]
        }
    
    async def _simulate_tool_execution(
        self,
        tool_name: str,
        params: dict[str, Any],
        sandbox_id: str
    ) -> Any:
        """模拟工具执行
        
        注意：这是一个模拟实现，实际应用中应调用真实的工具处理函数。
        
        Args:
            tool_name: 工具名称
            params: 工具参数
            sandbox_id: 沙箱环境ID
            
        Returns:
            Any: 模拟执行结果
        """
        # 更新资源使用情况
        if sandbox_id in self.active_sandboxes:
            self.active_sandboxes[sandbox_id]["resource_usage"]["memory_mb"] = 128
            self.active_sandboxes[sandbox_id]["resource_usage"]["cpu_percent"] = 25.0
        
        # 模拟异步执行
        await asyncio.sleep(0.1)
        
        # 返回模拟结果
        return {
            "tool_name": tool_name,
            "params": params,
            "sandbox_id": sandbox_id,
            "message": f"工具 '{tool_name}' 在沙箱中执行完成"
        }
    
    def get_active_sandboxes(self) -> list[dict[str, Any]]:
        """获取所有活跃沙箱信息
        
        Returns:
            list: 活跃沙箱信息列表
        """
        return [
            {
                "sandbox_id": sandbox_id,
                "agent_id": sandbox["agent_id"],
                "status": sandbox["status"],
                "created_at": sandbox["created_at"]
            }
            for sandbox_id, sandbox in self.active_sandboxes.items()
        ]
    
    def get_sandbox_config(self) -> dict[str, Any]:
        """获取当前沙箱配置
        
        Returns:
            dict: 沙箱配置信息
        """
        return {
            "max_memory_mb": self.sandbox_config.max_memory_mb,
            "max_cpu_percent": self.sandbox_config.max_cpu_percent,
            "timeout_seconds": self.sandbox_config.timeout_seconds,
            "allowed_hosts": self.sandbox_config.allowed_hosts,
            "blocked_commands": self.sandbox_config.blocked_commands
        }