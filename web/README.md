# Swagger API Agent Web Frontend

这是 Swagger API Agent 的前端界面，使用 React + Vite + Material-UI 构建。

## 功能特性

- 🤖 **智能对话界面** - 通过自然语言与API进行交互
- 📊 **实时状态监控** - 显示后端服务连接状态和API信息
- 🔧 **函数列表查看** - 浏览和搜索可用的API函数
- 💬 **对话历史管理** - 查看、清空对话记录
- 📱 **响应式设计** - 适配桌面和移动设备
- 🎨 **Material Design** - 现代化的用户界面

## 技术栈

- **React 19** - 用户界面框架
- **TypeScript** - 类型安全
- **Vite** - 快速构建工具
- **Material-UI** - UI组件库
- **Axios** - HTTP请求库

## 开发环境设置

### 前置要求

- Node.js 18+ 
- npm 或 yarn
- Docker (用于后端服务)

### 快速启动

1. **克隆项目并进入目录**
   ```bash
   cd swagger-api-agent
   ```

2. **设置环境变量**
   ```bash
   export DEEPSEEK_API_KEY="your-deepseek-api-key"
   ```

3. **启动前后端服务**
   ```bash
   ./start-dev.sh
   ```

   或者手动启动：

   ```bash
   # 启动后端
   docker-compose up -d swagger-web
   
   # 启动前端
   cd web
   npm install
   npm run dev
   ```

4. **访问应用**
   - 前端: http://localhost:5173
   - 后端API: http://localhost:5000

### 单独开发前端

如果你只需要开发前端：

```bash
cd web
npm install
npm run dev
```

确保后端服务在 http://localhost:5000 运行。

## 项目结构

```
web/
├── src/
│   ├── components/          # React组件
│   │   ├── MainLayout.tsx   # 主布局组件
│   │   ├── ChatInterface.tsx # 聊天界面
│   │   ├── ConnectionStatus.tsx # 连接状态
│   │   ├── ApiInfo.tsx      # API信息显示
│   │   └── FunctionsList.tsx # 函数列表
│   ├── context/            # React Context
│   │   └── AppContext.tsx  # 应用状态管理
│   ├── hooks/              # 自定义Hooks
│   │   └── useApp.ts       # 应用状态Hook
│   ├── services/           # API服务
│   │   └── api.ts          # 后端API调用
│   ├── App.tsx             # 根组件
│   └── main.tsx            # 入口文件
├── public/                 # 静态资源
├── package.json            # 依赖配置
├── vite.config.ts          # Vite配置
└── tsconfig.json           # TypeScript配置
```

## API接口说明

前端与后端通过以下API接口通信：

- `GET /health` - 健康检查
- `POST /api/process` - 处理自然语言输入
- `POST /api/call` - 直接调用函数
- `GET /api/functions` - 获取可用函数列表
- `GET /api/info` - 获取API信息
- `GET /api/history` - 获取对话历史
- `DELETE /api/history` - 清空对话历史
- `POST /api/auth` - 设置API认证

## 使用说明

### 基本使用

1. **连接检查** - 启动后会自动检查与后端的连接状态
2. **自然语言交互** - 在聊天框中输入自然语言描述你想要调用的API
3. **函数浏览** - 在左侧面板查看所有可用的API函数
4. **历史管理** - 查看之前的对话记录，可以清空历史

### 示例对话

```
用户: 获取用户信息
AI: 我将为您调用获取用户信息的API...

用户: 创建一个新用户，名字叫张三
AI: 正在创建用户张三...
```

## 开发指南

### 添加新组件

1. 在 `src/components/` 目录下创建新组件
2. 使用TypeScript和Material-UI组件
3. 通过useApp Hook访问全局状态

### 状态管理

应用使用React Context进行状态管理：

```typescript
import { useApp } from '../hooks/useApp';

const MyComponent = () => {
  const { state, dispatch } = useApp();
  
  // 访问状态
  const { isConnected, conversations } = state;
  
  // 更新状态
  dispatch({ type: 'SET_LOADING', payload: true });
};
```

### API调用

使用封装的API服务：

```typescript
import apiService from '../services/api';

const response = await apiService.processNaturalLanguage({
  message: "用户输入",
  context: {}
});
```

## 构建部署

### 开发构建

```bash
npm run build
```

### 预览构建结果

```bash
npm run preview
```

### 生产部署

构建完成后，`dist/` 目录包含所有静态文件，可以部署到任何静态文件服务器。

## 故障排除

### 常见问题

1. **无法连接后端**
   - 检查后端服务是否运行在 http://localhost:5000
   - 检查网络连接和防火墙设置

2. **环境变量问题**
   - 确保设置了 DEEPSEEK_API_KEY
   - 检查环境变量是否正确传递给Docker容器

3. **依赖安装失败**
   - 清除node_modules: `rm -rf node_modules package-lock.json`
   - 重新安装: `npm install`

4. **TypeScript错误**
   - 检查tsconfig.json配置
   - 确保所有类型定义正确

### 日志调试

- 前端日志：浏览器开发者工具Console
- 后端日志：`docker-compose logs swagger-web`

## 贡献指南

1. Fork项目
2. 创建功能分支
3. 提交代码
4. 创建Pull Request

## 许可证

本项目遵循项目根目录的LICENSE文件。
