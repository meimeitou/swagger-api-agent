# OpenAPI Mock Server

基于 `example_openapi.yaml` 的本地Mock服务器，用于模拟API接口进行开发和测试。

## 快速开始

### 1. 安装依赖

```bash
pip install flask flask-cors requests
```

### 2. 启动服务器

```bash
# 方法1: 直接运行Python脚本
python3 simple_mock_server.py

# 方法2: 使用启动脚本（会自动安装依赖）
./start_mock_server.sh

# 方法3: 自定义端口和主机
python3 simple_mock_server.py --host 0.0.0.0 --port 3000
```

### 3. 访问服务

服务启动后，访问以下地址：

- **API根路径**: http://127.0.0.1:8080/
- **健康检查**: http://127.0.0.1:8080/health
- **所有数据**: http://127.0.0.1:8080/data

## API接口

### 用户管理

| 方法 | 路径 | 描述 | 示例 |
|------|------|------|------|
| GET | `/users` | 获取用户列表 | `GET /users?page=1&limit=10&role=admin` |
| POST | `/users` | 创建用户 | 见下方示例 |
| GET | `/users/{id}` | 获取指定用户 | `GET /users/1` |
| PUT | `/users/{id}` | 更新用户信息 | 见下方示例 |
| DELETE | `/users/{id}` | 删除用户 | `DELETE /users/1` |

### 产品管理

| 方法 | 路径 | 描述 | 示例 |
|------|------|------|------|
| GET | `/products` | 获取产品列表 | `GET /products?category=electronics&min_price=100` |

### 订单管理

| 方法 | 路径 | 描述 | 示例 |
|------|------|------|------|
| POST | `/orders` | 创建订单 | 见下方示例 |

### 工具接口

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/health` | 健康检查 |
| POST | `/reset` | 重置所有数据 |
| GET | `/data` | 查看所有数据（调试用） |

## 使用示例

### 创建用户

```bash
curl -X POST http://127.0.0.1:8080/users \
  -H "Content-Type: application/json" \
  -d '{
    "name": "张三",
    "email": "zhangsan@example.com",
    "role": "user"
  }'
```

### 获取用户列表（带筛选）

```bash
# 获取第1页，每页5个用户
curl "http://127.0.0.1:8080/users?page=1&limit=5"

# 筛选admin角色的用户
curl "http://127.0.0.1:8080/users?role=admin"
```

### 更新用户信息

```bash
curl -X PUT http://127.0.0.1:8080/users/1 \
  -H "Content-Type: application/json" \
  -d '{
    "name": "李四",
    "role": "admin"
  }'
```

### 获取产品列表（带筛选）

```bash
# 获取所有产品
curl "http://127.0.0.1:8080/products"

# 筛选电子产品
curl "http://127.0.0.1:8080/products?category=electronics"

# 搜索包含"iPhone"的产品
curl "http://127.0.0.1:8080/products?search=iPhone"

# 价格范围筛选
curl "http://127.0.0.1:8080/products?min_price=1000&max_price=6000"
```

### 创建订单

```bash
curl -X POST http://127.0.0.1:8080/orders \
  -H "Content-Type: application/json" \
  -d '{
    "userId": 1,
    "items": [
      {
        "productId": 1,
        "quantity": 2
      },
      {
        "productId": 2,
        "quantity": 1
      }
    ]
  }'
```

## 测试

运行自动化测试脚本：

```bash
# 确保mock服务器正在运行，然后执行：
python3 test_mock_server.py

# 或者指定自定义URL
python3 test_mock_server.py --url http://localhost:3000

# 等待服务器启动后再测试
python3 test_mock_server.py --wait 5
```

## 初始数据

服务器启动时会自动生成以下初始数据：

### 用户
- 5个用户：张三、李四、王五、赵六、孙七
- 不同角色：admin、user、guest

### 产品
- 6个产品：iPhone 15、MacBook Pro、AirPods Pro、咖啡机、跑步鞋、平板电脑
- 不同分类：electronics、home、sports

### 订单
- 8个随机订单，包含不同状态

## 重置数据

如需重置所有数据到初始状态：

```bash
curl -X POST http://127.0.0.1:8080/reset
```

## 命令行参数

```bash
python3 simple_mock_server.py --help
```

可用参数：
- `--host`: 服务器主机地址（默认：127.0.0.1）
- `--port`: 服务器端口（默认：8080）
- `--debug`: 启用调试模式

## 注意事项

1. 这是一个内存型Mock服务器，重启后数据会丢失
2. 数据在内存中保存，适合开发和测试使用
3. 支持CORS，可以从浏览器直接调用
4. 所有接口都返回JSON格式的响应
5. 包含基本的数据验证和错误处理

## 故障排除

### 端口被占用
```bash
# 查看端口占用
lsof -i :8080

# 使用其他端口
python3 simple_mock_server.py --port 8081
```

### 依赖安装问题
```bash
# 确保pip是最新版本
pip install --upgrade pip

# 重新安装依赖
pip install flask flask-cors requests
```

### 连接问题
```bash
# 检查服务器是否正在运行
curl http://127.0.0.1:8080/health

# 检查防火墙设置（如果使用0.0.0.0监听）
```
