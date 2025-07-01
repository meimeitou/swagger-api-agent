# 多用户会话管理

Swagger API Agent 现在支持多用户独立会话管理，每个用户登录后都会获得独立的 Agent 实例和对话上下文。

## 功能特性

### 🔐 用户隔离
- 每个用户拥有独立的 Agent 实例
- 独立的对话历史和上下文
- 用户数据完全隔离，互不干扰

### 🎯 会话管理
- 自动会话创建和初始化
- 会话超时自动清理（24小时）
- 支持手动重置用户会话
- 实时会话状态监控

### 📊 管理功能
- 会话统计信息查询
- 所有会话信息管理
- 过期会话手动清理
- 会话活动状态监控

## API 接口

### 认证相关

#### 用户登录
```http
POST /api/login
Content-Type: application/json

{
    "username": "your_username",
    "password": "your_password"
}
```

响应：
```json
{
    "success": true,
    "message": "登录成功",
    "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "expires_in": 86400
}
```

### API 调用（需要认证）

所有以下接口都需要在请求头中包含JWT token：
```
Authorization: Bearer <your_jwt_token>
```

#### 处理自然语言输入
```http
POST /api/process
Content-Type: application/json
Authorization: Bearer <token>

{
    "message": "获取用户列表",
    "context": {
        "additional_info": "any context"
    }
}
```

#### 直接调用API函数
```http
POST /api/call
Content-Type: application/json
Authorization: Bearer <token>

{
    "function_name": "getUserList",
    "parameters": {
        "page": 1,
        "limit": 10
    }
}
```

#### 获取可用函数列表
```http
GET /api/functions
Authorization: Bearer <token>
```

#### 获取API信息
```http
GET /api/info
Authorization: Bearer <token>
```

### 对话管理

#### 获取对话历史
```http
GET /api/history
Authorization: Bearer <token>
```

#### 清空对话历史
```http
DELETE /api/history
Authorization: Bearer <token>
```

### 会话管理

#### 获取当前用户会话信息
```http
GET /api/session/info
Authorization: Bearer <token>
```

响应：
```json
{
    "success": true,
    "session_info": {
        "user_id": "username",
        "session_id": "uuid",
        "created_at": "2025-07-01T10:00:00",
        "last_active": "2025-07-01T10:30:00",
        "is_active": true,
        "conversation_length": 5,
        "agent_status": {
            "initialized": true,
            "openapi_file": "/path/to/openapi.yaml",
            "api_base_url": "https://api.example.com",
            "llm_available": true
        }
    }
}
```

#### 重置当前用户会话
```http
POST /api/session/reset
Authorization: Bearer <token>
```

这将：
- 关闭当前会话
- 创建新的 Agent 实例
- 清空对话历史
- 返回新会话信息

### 管理员功能

#### 获取所有会话信息
```http
GET /api/admin/sessions
Authorization: Bearer <token>
```

响应：
```json
{
    "success": true,
    "sessions_info": {
        "total_sessions": 3,
        "active_sessions": 2,
        "sessions": {
            "user1": {
                "user_id": "user1",
                "session_id": "uuid1",
                "created_at": "2025-07-01T09:00:00",
                "last_active": "2025-07-01T10:00:00",
                "is_active": true,
                "conversation_length": 3
            },
            "user2": {
                "user_id": "user2", 
                "session_id": "uuid2",
                "created_at": "2025-07-01T09:30:00",
                "last_active": "2025-07-01T10:15:00",
                "is_active": true,
                "conversation_length": 7
            }
        }
    }
}
```

#### 手动清理过期会话
```http
POST /api/admin/cleanup
Authorization: Bearer <token>
```

### 系统信息

#### 健康检查
```http
GET /health
```

响应包含会话统计信息：
```json
{
    "status": "healthy",
    "service": "Swagger API Agent",
    "timestamp": "2025-07-01T10:30:00",
    "session_stats": {
        "total_sessions": 3,
        "active_sessions": 2,
        "inactive_sessions": 1,
        "session_timeout_hours": 24,
        "last_cleanup": "2025-07-01T09:00:00"
    },
    "config_valid": true,
    "api_base_url": "https://api.example.com",
    "openapi_file": "/path/to/openapi.yaml"
}
```

## 使用场景

### 1. 多用户同时使用
```bash
# 用户A登录
curl -X POST http://localhost:5000/api/login \
  -H "Content-Type: application/json" \
  -d '{"username": "userA", "password": "password"}'

# 用户B登录
curl -X POST http://localhost:5000/api/login \
  -H "Content-Type: application/json" \
  -d '{"username": "userB", "password": "password"}'

# 每个用户都有独立的对话历史和上下文
```

### 2. 会话管理
```bash
# 查看会话信息
curl -X GET http://localhost:5000/api/session/info \
  -H "Authorization: Bearer <user_token>"

# 重置会话（清空对话历史，重新初始化）
curl -X POST http://localhost:5000/api/session/reset \
  -H "Authorization: Bearer <user_token>"
```

### 3. 管理员监控
```bash
# 查看所有用户会话
curl -X GET http://localhost:5000/api/admin/sessions \
  -H "Authorization: Bearer <admin_token>"

# 手动清理过期会话
curl -X POST http://localhost:5000/api/admin/cleanup \
  -H "Authorization: Bearer <admin_token>"
```

## 配置说明

### 环境变量
```bash
# JWT配置
JWT_SECRET_KEY=your_secret_key_here
JWT_EXPIRATION_HOURS=24

# 用户认证
WEB_API_USERNAME=admin
WEB_API_PASSWORD=your_password

# API配置
OPENAPI_FILE=/path/to/your/openapi.yaml
API_BASE_URL=https://your-api.example.com
API_TOKEN=your_api_token
DEEPSEEK_API_KEY=your_deepseek_key
```

### 会话超时配置
在 `user_session_manager.py` 中可以调整：
```python
class UserSessionManager:
    def __init__(self):
        self.session_timeout = timedelta(hours=24)  # 24小时超时
        self.cleanup_interval = timedelta(hours=1)  # 1小时清理一次
```

## 架构说明

### 会话管理器
- **单例模式**：全局唯一的会话管理器实例
- **线程安全**：使用锁机制保证并发安全
- **自动清理**：定期清理过期会话释放资源

### 用户会话
- **独立实例**：每个用户都有独立的 Agent 实例
- **状态隔离**：用户间的对话历史完全隔离
- **活动跟踪**：实时跟踪用户活动时间

### 认证机制
- **JWT Token**：无状态的用户认证
- **自动注入**：认证通过后自动获取用户Agent
- **权限控制**：可扩展的权限验证机制

## 注意事项

1. **内存使用**：每个用户都有独立的Agent实例，会消耗更多内存
2. **会话清理**：确保设置合适的超时时间避免内存泄漏
3. **并发处理**：大量并发用户时注意系统资源监控
4. **数据持久化**：当前会话数据不持久化，重启服务会丢失
5. **配置共享**：所有用户共享相同的OpenAPI文档和API配置

## 扩展功能

未来可以扩展的功能：
- 会话数据持久化到数据库
- 用户权限分级管理
- 会话数据导出/导入
- 用户自定义配置
- 会话共享和协作功能
