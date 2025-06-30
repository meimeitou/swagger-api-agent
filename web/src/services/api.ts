import axios from 'axios';

const api = axios.create({
  headers: {
    'Content-Type': 'application/json',
  },
});

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

// 认证设置请求
export interface AuthRequest {
  auth_type: string;
  [key: string]: unknown;
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
    const response = await api.get<ApiResponse<ConversationMessage[]>>('/api/history');
    return response.data;
  }

  // 清空对话历史
  async clearConversationHistory(): Promise<ApiResponse> {
    const response = await api.delete<ApiResponse>('/api/history');
    return response.data;
  }

  // 设置API认证
  async setApiAuth(request: AuthRequest): Promise<ApiResponse> {
    const response = await api.post<ApiResponse>('/api/auth', request);
    return response.data;
  }
}

export const apiService = new ApiService();
export default apiService;
