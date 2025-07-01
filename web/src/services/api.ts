import axios from 'axios';

const api = axios.create({
  headers: {
    'Content-Type': 'application/json',
  },
});

// JWT token管理
class TokenManager {
  private static readonly TOKEN_KEY = 'swagger_api_token';

  static getToken(): string | null {
    return localStorage.getItem(this.TOKEN_KEY);
  }

  static setToken(token: string): void {
    localStorage.setItem(this.TOKEN_KEY, token);
  }

  static removeToken(): void {
    localStorage.removeItem(this.TOKEN_KEY);
  }

  static isTokenValid(): boolean {
    const token = this.getToken();
    if (!token) return false;

    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      const exp = payload.exp * 1000; // 转换为毫秒
      return Date.now() < exp;
    } catch {
      return false;
    }
  }
}

// 请求拦截器 - 自动添加认证token
api.interceptors.request.use(
  (config) => {
    const token = TokenManager.getToken();
    if (token && TokenManager.isTokenValid()) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器 - 处理401未授权响应
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      console.warn('认证失败，清除token并触发登录流程');
      TokenManager.removeToken();
      // 触发认证过期事件，让组件处理登录跳转
      window.dispatchEvent(new CustomEvent('auth-expired'));
    }
    return Promise.reject(error);
  }
);

// API响应接口
export interface ApiResponse<T = unknown> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

// 自然语言处理请求
export interface ProcessRequest {
  message: string;
  context?: Record<string, unknown>;
}

// 函数调用请求
export interface FunctionCallRequest {
  function_name: string;
  parameters?: Record<string, unknown>;
}

// 登录请求和响应接口
export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  success: boolean;
  token?: string;
  message?: string;
  expires_in?: number;
  error?: string;
}

// API函数信息
export interface ApiFunction {
  name: string;
  description?: string;
  parameters?: Record<string, unknown>;
  responses?: Record<string, unknown>;
}

// 对话历史消息
export interface ConversationMessage {
  role: string;
  content: string;
  timestamp: string;
}

// 健康检查响应
export interface HealthResponse {
  status: string;
  agent_initialized: boolean;
  timestamp?: string;
  api_title?: string;
  api_version?: string;
  endpoints_count?: number;
}

// API信息响应
export interface ApiInfoResponse {
  api_info: {
    title: string;
    version: string;
    description?: string;
    endpoints_count: number;
  };
  agent_status: {
    initialized: boolean;
    last_error?: string;
  };
}

class ApiService {
  // 用户登录
  async login(request: LoginRequest): Promise<LoginResponse> {
    const response = await api.post<LoginResponse>('/api/login', request);
    
    // 如果登录成功，保存token
    if (response.data.success && response.data.token) {
      TokenManager.setToken(response.data.token);
    }
    
    return response.data;
  }

  // 用户登出
  logout(): void {
    TokenManager.removeToken();
  }

  // 检查是否已登录
  isAuthenticated(): boolean {
    const isValid = TokenManager.isTokenValid();
    if (!isValid && TokenManager.getToken()) {
      // 如果token存在但无效（过期），清除它
      console.warn('Token 已过期，清除无效token');
      TokenManager.removeToken();
      window.dispatchEvent(new CustomEvent('auth-expired'));
    }
    return isValid;
  }

  // 健康检查
  async healthCheck(): Promise<HealthResponse> {
    const response = await api.get<HealthResponse>('/health');
    return response.data;
  }

  // 处理自然语言输入
  async processNaturalLanguage(request: ProcessRequest): Promise<ApiResponse> {
    const response = await api.post<ApiResponse>('/api/process', request);
    return response.data;
  }

  // 直接调用函数
  async callFunction(request: FunctionCallRequest): Promise<ApiResponse> {
    const response = await api.post<ApiResponse>('/api/call', request);
    return response.data;
  }

  // 获取可用函数列表
  async getFunctions(): Promise<ApiResponse<ApiFunction[]>> {
    const response = await api.get<{success: boolean, functions: ApiFunction[], count: number}>('/api/functions');
    // 转换后端响应格式以匹配前端期望
    return {
      success: response.data.success,
      data: response.data.functions,
      message: `成功获取 ${response.data.count} 个函数`
    };
  }

  // 获取API信息
  async getApiInfo(): Promise<ApiResponse<ApiInfoResponse>> {
    const response = await api.get<ApiResponse<ApiInfoResponse>>('/api/info');
    return response.data;
  }

  // 获取对话历史
  async getConversationHistory(): Promise<ApiResponse<ConversationMessage[]>> {
    const response = await api.get<{success: boolean, history: ConversationMessage[], count: number}>('/api/history');
    // 转换后端响应格式以匹配前端期望
    return {
      success: response.data.success,
      data: response.data.history,
      message: `成功获取 ${response.data.count} 条对话记录`
    };
  }

  // 清空对话历史
  async clearConversationHistory(): Promise<ApiResponse> {
    const response = await api.delete<ApiResponse>('/api/history');
    return response.data;
  }
}

export const apiService = new ApiService();
export { TokenManager };
export default apiService;
