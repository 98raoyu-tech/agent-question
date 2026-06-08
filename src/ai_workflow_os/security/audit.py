"""
审计日志模块

记录所有系统操作的审计日志，支持日志查询和报告生成。
提供缓冲机制优化写入性能。
"""

from dataclasses import dataclass, field
from typing import Any
from datetime import datetime, date
import asyncio
import uuid
import logging

# 配置日志记录器
logger = logging.getLogger(__name__)


@dataclass
class AuditEntry:
    """审计日志条目
    
    Attributes:
        entry_id: 日志条目唯一标识
        timestamp: 记录时间戳
        user_id: 操作用户ID
        agent_id: 操作Agent ID
        action: 操作类型
        resource: 资源类型
        resource_id: 资源ID
        details: 操作详情
        ip_address: 客户端IP地址
        result: 操作结果（success/failure/error）
        risk_level: 风险等级（low/medium/high/critical）
    """
    entry_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    user_id: str = ""
    agent_id: str = ""
    action: str = ""
    resource: str = ""
    resource_id: str = ""
    details: dict[str, Any] = field(default_factory=dict)
    ip_address: str = ""
    result: str = "success"
    risk_level: str = "low"


class AuditLogger:
    """审计日志记录器
    
    记录所有系统操作的审计日志，支持缓冲写入和日志查询。
    
    Attributes:
        storage_backend: 存储后端
        buffer: 日志缓冲区
        flush_interval: 缓冲区刷新间隔（秒）
    """
    
    def __init__(self, flush_interval: int = 60) -> None:
        """初始化审计日志记录器
        
        Args:
            flush_interval: 缓冲区刷新间隔（秒），默认60秒
        """
        self.storage_backend: dict[str, AuditEntry] = {}
        self.buffer: list[AuditEntry] = []
        self.flush_interval = flush_interval
        
        logger.info("审计日志记录器已初始化")
    
    async def log(self, entry: AuditEntry) -> None:
        """记录审计日志
        
        Args:
            entry: 审计日志条目
        """
        # 添加到缓冲区
        self.buffer.append(entry)
        
        # 如果缓冲区达到阈值，立即刷新
        if len(self.buffer) >= 100:
            await self.flush()
        
        logger.debug(
            f"审计日志已记录: {entry.action} on {entry.resource} "
            f"by {entry.user_id or entry.agent_id}"
        )
    
    async def log_agent_action(
        self,
        agent_id: str,
        action: str,
        resource: str,
        result: str = "success"
    ) -> None:
        """记录Agent操作
        
        Args:
            agent_id: Agent ID
            action: 操作类型
            resource: 资源类型
            result: 操作结果
        """
        entry = AuditEntry(
            agent_id=agent_id,
            action=action,
            resource=resource,
            result=result
        )
        
        await self.log(entry)
    
    async def log_user_action(
        self,
        user_id: str,
        action: str,
        resource: str,
        result: str = "success"
    ) -> None:
        """记录用户操作
        
        Args:
            user_id: 用户ID
            action: 操作类型
            resource: 资源类型
            result: 操作结果
        """
        entry = AuditEntry(
            user_id=user_id,
            action=action,
            resource=resource,
            result=result
        )
        
        await self.log(entry)
    
    async def log_security_event(
        self,
        event_type: str,
        details: dict[str, Any]
    ) -> None:
        """记录安全事件
        
        Args:
            event_type: 事件类型
            details: 事件详情
        """
        entry = AuditEntry(
            action=event_type,
            resource="security",
            details=details,
            risk_level=details.get("risk_level", "high"),
            result=details.get("result", "warning")
        )
        
        await self.log(entry)
        
        logger.warning(f"安全事件已记录: {event_type}")
    
    async def query(
        self,
        filters: dict[str, Any] | None = None,
        limit: int = 100
    ) -> list[AuditEntry]:
        """查询审计日志
        
        Args:
            filters: 过滤条件，支持字段匹配
            limit: 返回结果数量限制
            
        Returns:
            list: 匹配的审计日志条目列表
        """
        # 先刷新缓冲区
        await self.flush()
        
        # 获取所有日志
        all_entries = list(self.storage_backend.values())
        
        # 如果没有过滤条件，返回所有日志
        if not filters:
            return sorted(
                all_entries,
                key=lambda e: e.timestamp,
                reverse=True
            )[:limit]
        
        # 应用过滤条件
        filtered_entries = []
        for entry in all_entries:
            match = True
            
            for field_name, filter_value in filters.items():
                entry_value = getattr(entry, field_name, None)
                
                if entry_value is None:
                    match = False
                    break
                
                # 支持字符串包含匹配
                if isinstance(filter_value, str) and isinstance(entry_value, str):
                    if filter_value.lower() not in entry_value.lower():
                        match = False
                        break
                # 精确匹配
                elif entry_value != filter_value:
                    match = False
                    break
            
            if match:
                filtered_entries.append(entry)
        
        # 按时间排序并限制数量
        return sorted(
            filtered_entries,
            key=lambda e: e.timestamp,
            reverse=True
        )[:limit]
    
    async def flush(self) -> None:
        """将缓冲区日志写入存储"""
        if not self.buffer:
            return
        
        # 将缓冲区日志写入存储
        for entry in self.buffer:
            self.storage_backend[entry.entry_id] = entry
        
        # 清空缓冲区
        flushed_count = len(self.buffer)
        self.buffer = []
        
        logger.debug(f"已刷新 {flushed_count} 条审计日志到存储")
    
    async def generate_report(
        self,
        start_date: date | None = None,
        end_date: date | None = None
    ) -> dict[str, Any]:
        """生成审计报告
        
        Args:
            start_date: 报告开始日期
            end_date: 报告结束日期
            
        Returns:
            dict: 审计报告
        """
        # 先刷新缓冲区
        await self.flush()
        
        # 获取所有日志
        all_entries = list(self.storage_backend.values())
        
        # 按日期过滤
        filtered_entries = []
        for entry in all_entries:
            entry_date = entry.timestamp.date()
            
            if start_date and entry_date < start_date:
                continue
            if end_date and entry_date > end_date:
                continue
            
            filtered_entries.append(entry)
        
        # 统计操作类型分布
        action_counts: dict[str, int] = {}
        for entry in filtered_entries:
            action_counts[entry.action] = action_counts.get(entry.action, 0) + 1
        
        # 统计资源类型分布
        resource_counts: dict[str, int] = {}
        for entry in filtered_entries:
            resource_counts[entry.resource] = resource_counts.get(entry.resource, 0) + 1
        
        # 统计操作结果分布
        result_counts: dict[str, int] = {}
        for entry in filtered_entries:
            result_counts[entry.result] = result_counts.get(entry.result, 0) + 1
        
        # 统计风险等级分布
        risk_counts: dict[str, int] = {}
        for entry in filtered_entries:
            risk_counts[entry.risk_level] = risk_counts.get(entry.risk_level, 0) + 1
        
        # 统计用户操作数量
        user_counts: dict[str, int] = {}
        for entry in filtered_entries:
            user_id = entry.user_id or entry.agent_id
            if user_id:
                user_counts[user_id] = user_counts.get(user_id, 0) + 1
        
        return {
            "period": {
                "start_date": start_date.isoformat() if start_date else "N/A",
                "end_date": end_date.isoformat() if end_date else "N/A"
            },
            "total_entries": len(filtered_entries),
            "action_distribution": action_counts,
            "resource_distribution": resource_counts,
            "result_distribution": result_counts,
            "risk_distribution": risk_counts,
            "top_users": dict(
                sorted(user_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            )
        }
    
    def get_statistics(self) -> dict[str, Any]:
        """获取审计日志统计信息
        
        Returns:
            dict: 统计信息
        """
        return {
            "total_entries": len(self.storage_backend),
            "buffer_size": len(self.buffer),
            "flush_interval": self.flush_interval
        }
    
    async def clear(self) -> int:
        """清空所有审计日志
        
        Returns:
            int: 清除的日志数量
        """
        count = len(self.storage_backend) + len(self.buffer)
        
        self.storage_backend.clear()
        self.buffer.clear()
        
        logger.info(f"已清空 {count} 条审计日志")
        return count
    
    async def get_entry(self, entry_id: str) -> AuditEntry | None:
        """获取指定日志条目
        
        Args:
            entry_id: 日志条目ID
            
        Returns:
            AuditEntry: 日志条目，不存在返回None
        """
        # 先检查缓冲区
        for entry in self.buffer:
            if entry.entry_id == entry_id:
                return entry
        
        # 再检查存储
        return self.storage_backend.get(entry_id)