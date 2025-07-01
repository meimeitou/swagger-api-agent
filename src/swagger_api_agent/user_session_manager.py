"""
用户会话管理器
为每个用户维护独立的 Swagger API Agent 实例和对话上下文
"""

import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, Optional
from uuid import uuid4

from .agent import SwaggerAPIAgent

logger = logging.getLogger(__name__)


class UserSession:
    """用户会话类"""
    
    def __init__(self, user_id: str, agent: SwaggerAPIAgent):
        self.user_id = user_id
        self.agent = agent
        self.session_id = str(uuid4())
        self.created_at = datetime.now()
        self.last_active = datetime.now()
        self.is_active = True
    
    def update_activity(self):
        """更新最后活动时间"""
        self.last_active = datetime.now()
    
    def get_session_info(self) -> Dict:
        """获取会话信息"""
        return {
            "user_id": self.user_id,
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "last_active": self.last_active.isoformat(),
            "is_active": self.is_active,
            "conversation_length": len(self.agent.get_conversation_history()) if self.agent else 0,
            "agent_status": self.agent.get_status() if self.agent else {}
        }


class UserSessionManager:
    """用户会话管理器 - 单例模式"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(UserSessionManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.sessions: Dict[str, UserSession] = {}
            self.session_timeout = timedelta(hours=24)  # 24小时超时
            self.cleanup_interval = timedelta(hours=1)  # 1小时清理一次
            self.last_cleanup = datetime.now()
            self._lock = threading.RLock()
            self.initialized = True
            logger.info("用户会话管理器初始化完成")
    
    def create_user_session(
        self, 
        user_id: str, 
        openapi_file: str = None,
        api_base_url: str = None,
        api_token: str = None,
        deepseek_api_key: str = None,
        force_new: bool = False
    ) -> UserSession:
        """
        为用户创建新的会话
        
        Args:
            user_id: 用户ID
            openapi_file: OpenAPI 文档路径
            api_base_url: API 基础 URL  
            api_token: API 认证 Token
            deepseek_api_key: DeepSeek API 密钥
            force_new: 是否强制创建新会话（即使已存在）
            
        Returns:
            用户会话对象
        """
        with self._lock:
            # 如果用户已有活跃会话且不强制创建新会话，返回现有会话
            if user_id in self.sessions and not force_new:
                existing_session = self.sessions[user_id]
                if existing_session.is_active:
                    existing_session.update_activity()
                    logger.info(f"返回用户 {user_id} 的现有会话: {existing_session.session_id}")
                    return existing_session
            
            # 创建新的 agent 实例
            agent = SwaggerAPIAgent(
                openapi_file=openapi_file,
                api_base_url=api_base_url,
                api_token=api_token,
                deepseek_api_key=deepseek_api_key
            )
            
            # 初始化 agent
            if not agent.initialize():
                logger.error(f"为用户 {user_id} 初始化 agent 失败: {agent.last_error}")
                raise RuntimeError(f"Agent 初始化失败: {agent.last_error}")
            
            # 创建用户会话
            session = UserSession(user_id, agent)
            self.sessions[user_id] = session
            
            logger.info(f"为用户 {user_id} 创建新会话: {session.session_id}")
            return session
    
    def get_user_session(self, user_id: str) -> Optional[UserSession]:
        """
        获取用户会话
        
        Args:
            user_id: 用户ID
            
        Returns:
            用户会话对象，如果不存在则返回 None
        """
        with self._lock:
            session = self.sessions.get(user_id)
            if session and session.is_active:
                session.update_activity()
                return session
            return None
    
    def get_user_agent(self, user_id: str) -> Optional[SwaggerAPIAgent]:
        """
        获取用户的 agent 实例
        
        Args:
            user_id: 用户ID
            
        Returns:
            SwaggerAPIAgent 实例，如果不存在则返回 None
        """
        session = self.get_user_session(user_id)
        return session.agent if session else None
    
    def close_user_session(self, user_id: str) -> bool:
        """
        关闭用户会话
        
        Args:
            user_id: 用户ID
            
        Returns:
            是否成功关闭
        """
        with self._lock:
            if user_id in self.sessions:
                session = self.sessions[user_id]
                session.is_active = False
                # 清理对话历史
                if session.agent:
                    session.agent.clear_conversation_history()
                del self.sessions[user_id]
                logger.info(f"关闭用户 {user_id} 的会话: {session.session_id}")
                return True
            return False
    
    def cleanup_expired_sessions(self):
        """清理过期的会话"""
        with self._lock:
            current_time = datetime.now()
            expired_users = []
            
            for user_id, session in self.sessions.items():
                if current_time - session.last_active > self.session_timeout:
                    expired_users.append(user_id)
            
            for user_id in expired_users:
                self.close_user_session(user_id)
                logger.info(f"清理过期会话: 用户 {user_id}")
            
            if expired_users:
                logger.info(f"清理了 {len(expired_users)} 个过期会话")
            
            self.last_cleanup = current_time
    
    def auto_cleanup_if_needed(self):
        """如果需要，自动执行清理"""
        if datetime.now() - self.last_cleanup > self.cleanup_interval:
            self.cleanup_expired_sessions()
    
    def get_all_sessions_info(self) -> Dict:
        """获取所有会话信息"""
        with self._lock:
            self.auto_cleanup_if_needed()
            
            return {
                "total_sessions": len(self.sessions),
                "active_sessions": sum(1 for s in self.sessions.values() if s.is_active),
                "sessions": {
                    user_id: session.get_session_info() 
                    for user_id, session in self.sessions.items()
                }
            }
    
    def get_session_stats(self) -> Dict:
        """获取会话统计信息"""
        with self._lock:
            total = len(self.sessions)
            active = sum(1 for s in self.sessions.values() if s.is_active)
            
            return {
                "total_sessions": total,
                "active_sessions": active,
                "inactive_sessions": total - active,
                "session_timeout_hours": self.session_timeout.total_seconds() / 3600,
                "last_cleanup": self.last_cleanup.isoformat()
            }


# 全局会话管理器实例
session_manager = UserSessionManager()


def get_session_manager() -> UserSessionManager:
    """获取全局会话管理器实例"""
    return session_manager


def get_or_create_user_agent(
    user_id: str,
    openapi_file: str = None,
    api_base_url: str = None, 
    api_token: str = None,
    deepseek_api_key: str = None,
    force_new: bool = False
) -> SwaggerAPIAgent:
    """
    获取或创建用户的 agent 实例（便捷函数）
    
    Args:
        user_id: 用户ID
        openapi_file: OpenAPI 文档路径
        api_base_url: API 基础 URL
        api_token: API 认证 Token
        deepseek_api_key: DeepSeek API 密钥
        force_new: 是否强制创建新会话
        
    Returns:
        SwaggerAPIAgent 实例
    """
    session_manager = get_session_manager()
    
    # 先尝试获取现有会话
    if not force_new:
        existing_agent = session_manager.get_user_agent(user_id)
        if existing_agent:
            return existing_agent
    
    # 创建新会话
    session = session_manager.create_user_session(
        user_id=user_id,
        openapi_file=openapi_file,
        api_base_url=api_base_url,
        api_token=api_token,
        deepseek_api_key=deepseek_api_key,
        force_new=force_new
    )
    
    return session.agent
