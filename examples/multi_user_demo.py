#!/usr/bin/env python3
"""
多用户会话功能示例

演示如何使用 Swagger API Agent 的多用户会话管理功能
"""

import json
import time
import requests
from typing import Dict, Optional

class SwaggerAPIAgentClient:
    """Swagger API Agent 客户端"""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.token: Optional[str] = None
        self.username: Optional[str] = None
    
    def login(self, username: str, password: str) -> Dict:
        """用户登录"""
        response = self.session.post(
            f"{self.base_url}/api/login",
            json={"username": username, "password": password}
        )
        
        result = response.json()
        if result.get("success"):
            self.token = result["token"]
            self.username = username
            # 设置认证头
            self.session.headers.update({
                "Authorization": f"Bearer {self.token}"
            })
            print(f"✅ 用户 {username} 登录成功")
        else:
            print(f"❌ 登录失败: {result.get('error')}")
        
        return result
    
    def process_message(self, message: str, context: Dict = None) -> Dict:
        """处理自然语言消息"""
        if not self.token:
            return {"success": False, "error": "请先登录"}
        
        response = self.session.post(
            f"{self.base_url}/api/process",
            json={
                "message": message,
                "context": context or {}
            }
        )
        
        result = response.json()
        if result.get("success"):
            print(f"🤖 [{self.username}] 处理成功")
            if result.get("message"):
                print(f"📝 回复: {result['message'][:200]}...")
        else:
            print(f"❌ [{self.username}] 处理失败: {result.get('error')}")
        
        return result
    
    def get_session_info(self) -> Dict:
        """获取会话信息"""
        if not self.token:
            return {"success": False, "error": "请先登录"}
        
        response = self.session.get(f"{self.base_url}/api/session/info")
        result = response.json()
        
        if result.get("success"):
            session_info = result["session_info"]
            print(f"📊 [{self.username}] 会话信息:")
            print(f"   - 会话ID: {session_info['session_id'][:8]}...")
            print(f"   - 创建时间: {session_info['created_at']}")
            print(f"   - 对话长度: {session_info['conversation_length']}")
            print(f"   - 状态: {'活跃' if session_info['is_active'] else '非活跃'}")
        
        return result
    
    def get_conversation_history(self) -> Dict:
        """获取对话历史"""
        if not self.token:
            return {"success": False, "error": "请先登录"}
        
        response = self.session.get(f"{self.base_url}/api/history")
        result = response.json()
        
        if result.get("success"):
            history = result["history"]
            print(f"💬 [{self.username}] 对话历史 ({len(history)} 条)")
            for i, msg in enumerate(history[-3:], 1):  # 显示最后3条
                role = "用户" if msg["role"] == "user" else "助手"
                content = msg["content"][:50] + "..." if len(msg["content"]) > 50 else msg["content"]
                print(f"   {i}. {role}: {content}")
        
        return result
    
    def reset_session(self) -> Dict:
        """重置会话"""
        if not self.token:
            return {"success": False, "error": "请先登录"}
        
        response = self.session.post(f"{self.base_url}/api/session/reset")
        result = response.json()
        
        if result.get("success"):
            print(f"🔄 [{self.username}] 会话已重置")
        else:
            print(f"❌ [{self.username}] 重置失败: {result.get('error')}")
        
        return result
    
    def get_functions(self) -> Dict:
        """获取可用函数"""
        if not self.token:
            return {"success": False, "error": "请先登录"}
        
        response = self.session.get(f"{self.base_url}/api/functions")
        result = response.json()
        
        if result.get("success"):
            functions = result["functions"]
            print(f"🔧 [{self.username}] 可用函数 ({len(functions)} 个)")
            for func in functions[:3]:  # 显示前3个
                print(f"   - {func['name']}: {func['description'][:50]}...")
        
        return result


def demo_multi_user_sessions():
    """演示多用户会话功能"""
    print("🚀 开始多用户会话演示\n")
    
    # 检查服务健康状态
    try:
        response = requests.get("http://localhost:5000/health")
        health = response.json()
        print(f"📡 服务状态: {health['status']}")
        print(f"📊 会话统计: {health['session_stats']}")
        print()
    except Exception as e:
        print(f"❌ 无法连接到服务: {e}")
        print("请确保 Swagger API Agent Web 服务正在运行")
        return
    
    # 创建多个用户客户端
    user_a = SwaggerAPIAgentClient()
    user_b = SwaggerAPIAgentClient()
    
    print("=" * 50)
    print("1. 用户登录演示")
    print("=" * 50)
    
    # 用户A登录
    user_a.login("admin", "password123")  # 使用默认的用户名密码
    time.sleep(1)
    
    # 用户B也使用相同的用户名登录（模拟同一用户的不同设备）
    user_b.login("admin", "password123")
    time.sleep(1)
    
    print("\n" + "=" * 50)
    print("2. 用户独立操作演示")
    print("=" * 50)
    
    # 用户A进行操作
    print(f"\n👤 用户A操作:")
    user_a.get_functions()
    user_a.process_message("获取API信息")
    user_a.get_session_info()
    
    time.sleep(2)
    
    # 用户B进行不同的操作
    print(f"\n👤 用户B操作:")
    user_b.get_functions()
    user_b.process_message("显示可用的API端点")
    user_b.get_session_info()
    
    print("\n" + "=" * 50)
    print("3. 对话历史独立性演示")
    print("=" * 50)
    
    # 查看各自的对话历史
    print(f"\n📚 用户A的对话历史:")
    user_a.get_conversation_history()
    
    print(f"\n📚 用户B的对话历史:")
    user_b.get_conversation_history()
    
    print("\n" + "=" * 50)
    print("4. 会话管理演示")
    print("=" * 50)
    
    # 用户A重置会话
    print(f"\n🔄 用户A重置会话:")
    user_a.reset_session()
    user_a.get_session_info()
    
    # 用户B继续使用原会话
    print(f"\n▶️  用户B继续对话:")
    user_b.process_message("再次查询API状态")
    user_b.get_conversation_history()
    
    print("\n" + "=" * 50)
    print("5. 管理员功能演示")
    print("=" * 50)
    
    # 查看所有会话信息（需要管理员权限）
    try:
        admin_client = SwaggerAPIAgentClient()
        admin_client.login("admin", "password123")
        
        response = admin_client.session.get("http://localhost:5000/api/admin/sessions")
        result = response.json()
        
        if result.get("success"):
            sessions = result["sessions_info"]
            print(f"👥 管理员视图 - 所有会话:")
            print(f"   总会话数: {sessions['total_sessions']}")
            print(f"   活跃会话: {sessions['active_sessions']}")
            
            for user_id, session_data in sessions.get("sessions", {}).items():
                print(f"   - 用户 {user_id}: 对话 {session_data['conversation_length']} 条")
        
    except Exception as e:
        print(f"❌ 管理员功能演示失败: {e}")
    
    print("\n" + "=" * 50)
    print("演示完成！")
    print("=" * 50)
    
    print("\n📋 总结:")
    print("✅ 每个用户都有独立的Agent实例")
    print("✅ 对话历史完全隔离")
    print("✅ 会话状态独立管理")
    print("✅ 支持会话重置和管理")
    print("✅ 管理员可以监控所有会话")


def demo_session_lifecycle():
    """演示会话生命周期"""
    print("\n🔄 会话生命周期演示")
    print("=" * 40)
    
    client = SwaggerAPIAgentClient()
    
    # 1. 登录创建会话
    print("1. 登录并创建会话")
    client.login("admin", "password123")
    client.get_session_info()
    
    # 2. 进行一些对话
    print("\n2. 进行对话")
    client.process_message("Hello, 这是测试消息1")
    client.process_message("这是测试消息2")
    client.get_conversation_history()
    
    # 3. 重置会话
    print("\n3. 重置会话")
    client.reset_session()
    client.get_conversation_history()  # 应该是空的
    
    # 4. 新会话中继续对话
    print("\n4. 新会话中对话")
    client.process_message("这是重置后的第一条消息")
    client.get_conversation_history()
    
    print("\n✅ 会话生命周期演示完成")


if __name__ == "__main__":
    print("🎯 Swagger API Agent 多用户会话功能演示")
    print("🔧 请确保服务运行在 http://localhost:5000")
    print("🔑 默认用户名: admin, 密码: password123")
    print()
    
    try:
        # 主要的多用户演示
        demo_multi_user_sessions()
        
        # 会话生命周期演示
        demo_session_lifecycle()
        
    except KeyboardInterrupt:
        print("\n👋 演示被用户中断")
    except Exception as e:
        print(f"\n💥 演示过程中出现错误: {e}")
        print("请检查服务是否正常运行，以及配置是否正确")
