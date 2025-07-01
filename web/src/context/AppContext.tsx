import React, { createContext, useReducer } from 'react';
import type { ReactNode } from 'react';
import type { ApiFunction, ConversationMessage, HealthResponse } from '../services/api';

// 应用状态接口
export interface AppState {
  // 认证状态
  isAuthenticated: boolean;
  
  // 用户信息
  userInfo: {
    username: string;
    loginTime: string;
  } | null;
  
  // 连接状态
  isConnected: boolean;
  isLoading: boolean;
  
  // API信息
  health: HealthResponse | null;
  functions: ApiFunction[];
  
  // 对话相关
  conversations: ConversationMessage[];
  currentMessage: string;
  
  // 错误信息
  error: string | null;
}

// 初始状态
const initialState: AppState = {
  isAuthenticated: false,
  userInfo: null,
  isConnected: false,
  isLoading: false,
  health: null,
  functions: [],
  conversations: [],
  currentMessage: '',
  error: null,
};

// Action类型
export type AppAction =
  | { type: 'SET_AUTHENTICATED'; payload: boolean }
  | { type: 'SET_USER_INFO'; payload: { username: string; loginTime: string } | null }
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_CONNECTED'; payload: boolean }
  | { type: 'SET_HEALTH'; payload: HealthResponse }
  | { type: 'SET_FUNCTIONS'; payload: ApiFunction[] }
  | { type: 'SET_CONVERSATIONS'; payload: ConversationMessage[] }
  | { type: 'ADD_CONVERSATION'; payload: ConversationMessage }
  | { type: 'SET_CURRENT_MESSAGE'; payload: string }
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'CLEAR_ERROR' };

// Reducer函数
function appReducer(state: AppState, action: AppAction): AppState {
  switch (action.type) {
    case 'SET_AUTHENTICATED':
      return { ...state, isAuthenticated: action.payload };
    case 'SET_USER_INFO':
      return { ...state, userInfo: action.payload };
    case 'SET_LOADING':
      return { ...state, isLoading: action.payload };
    case 'SET_CONNECTED':
      return { ...state, isConnected: action.payload };
    case 'SET_HEALTH':
      return { ...state, health: action.payload };
    case 'SET_FUNCTIONS':
      return { ...state, functions: action.payload };
    case 'SET_CONVERSATIONS':
      return { ...state, conversations: action.payload };
    case 'ADD_CONVERSATION':
      return { ...state, conversations: [...state.conversations, action.payload] };
    case 'SET_CURRENT_MESSAGE':
      return { ...state, currentMessage: action.payload };
    case 'SET_ERROR':
      return { ...state, error: action.payload };
    case 'CLEAR_ERROR':
      return { ...state, error: null };
    default:
      return state;
  }
}

// Context接口
interface AppContextType {
  state: AppState;
  dispatch: React.Dispatch<AppAction>;
}

// 创建Context
const AppContext = createContext<AppContextType | undefined>(undefined);

// Provider组件
interface AppProviderProps {
  children: ReactNode;
}

export const AppProvider: React.FC<AppProviderProps> = ({ children }) => {
  const [state, dispatch] = useReducer(appReducer, initialState);

  return (
    <AppContext.Provider value={{ state, dispatch }}>
      {children}
    </AppContext.Provider>
  );
};

export default AppContext;
