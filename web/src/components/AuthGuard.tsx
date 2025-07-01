import React, { useEffect } from 'react';
import { apiService } from '../services/api';
import { useApp } from '../hooks/useApp';
import LoginPage from './LoginPage';
import MainLayout from './MainLayout';

const AuthGuard: React.FC = () => {
  const { state, dispatch } = useApp();
  const { isAuthenticated } = state;

  useEffect(() => {
    // 检查初始认证状态
    const checkAuth = () => {
      const authenticated = apiService.isAuthenticated();
      dispatch({ type: 'SET_AUTHENTICATED', payload: authenticated });
      
      // 如果已认证，解析用户信息
      if (authenticated) {
        const token = localStorage.getItem('swagger_api_token');
        if (token) {
          try {
            const payload = JSON.parse(atob(token.split('.')[1]));
            dispatch({ 
              type: 'SET_USER_INFO', 
              payload: {
                username: payload.username,
                loginTime: new Date(payload.iat * 1000).toLocaleString('zh-CN')
              }
            });
          } catch (error) {
            console.error('Failed to parse token:', error);
          }
        }
      }
    };

    checkAuth();

    // 监听认证过期事件
    const handleAuthExpired = () => {
      dispatch({ type: 'SET_AUTHENTICATED', payload: false });
      dispatch({ type: 'SET_USER_INFO', payload: null });
      dispatch({ type: 'SET_ERROR', payload: '登录已过期，请重新登录' });
    };

    window.addEventListener('auth-expired', handleAuthExpired);

    return () => {
      window.removeEventListener('auth-expired', handleAuthExpired);
    };
  }, [dispatch]);

  const handleLoginSuccess = () => {
    dispatch({ type: 'SET_AUTHENTICATED', payload: true });
    dispatch({ type: 'CLEAR_ERROR' });
    
    // 解析并设置用户信息
    const token = localStorage.getItem('swagger_api_token');
    if (token) {
      try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        dispatch({ 
          type: 'SET_USER_INFO', 
          payload: {
            username: payload.username,
            loginTime: new Date(payload.iat * 1000).toLocaleString('zh-CN')
          }
        });
      } catch (error) {
        console.error('Failed to parse token:', error);
      }
    }
  };

  if (!isAuthenticated) {
    return <LoginPage onLoginSuccess={handleLoginSuccess} />;
  }

  return <MainLayout />;
};

export default AuthGuard;
