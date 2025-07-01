import React, { useEffect, useState } from 'react';
import { Box, CircularProgress, Typography } from '@mui/material';
import { apiService } from '../services/api';
import { useApp } from '../hooks/useApp';
import { useTokenCheck } from '../hooks/useTokenCheck';
import LoginPage from './LoginPage';
import MainLayout from './MainLayout';

const AuthGuard: React.FC = () => {
  const { state, dispatch } = useApp();
  const { isAuthenticated } = state;
  const [isCheckingAuth, setIsCheckingAuth] = useState(true);
  
  // 使用token检查hook（自动检查token过期）
  useTokenCheck();

  useEffect(() => {
    // 检查初始认证状态
    const checkAuth = async () => {
      try {
        console.log('检查用户认证状态...');
        
        const authenticated = apiService.isAuthenticated();
        console.log('认证状态:', authenticated);
        
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
              console.log('用户信息已设置:', payload.username);
            } catch (error) {
              console.error('Failed to parse token:', error);
              // 如果token解析失败，清除认证状态
              dispatch({ type: 'SET_AUTHENTICATED', payload: false });
            }
          }
        } else {
          // 确保清除用户信息
          dispatch({ type: 'SET_USER_INFO', payload: null });
        }
      } catch (error) {
        console.error('认证检查失败:', error);
        dispatch({ type: 'SET_AUTHENTICATED', payload: false });
        dispatch({ type: 'SET_USER_INFO', payload: null });
      } finally {
        setIsCheckingAuth(false);
      }
    };

    checkAuth();

    // 监听认证过期事件
    const handleAuthExpired = () => {
      console.warn('认证已过期，返回登录页面');
      dispatch({ type: 'SET_AUTHENTICATED', payload: false });
      dispatch({ type: 'SET_USER_INFO', payload: null });
      dispatch({ type: 'SET_CONNECTED', payload: false });
      dispatch({ type: 'SET_FUNCTIONS', payload: [] });
      dispatch({ type: 'SET_CONVERSATIONS', payload: [] });
      dispatch({ type: 'SET_ERROR', payload: '登录已过期，请重新登录' });
      setIsCheckingAuth(false);
    };

    // 监听存储变化（用于多标签页同步登出）
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === 'swagger_api_token' && !e.newValue) {
        console.log('检测到其他标签页登出，同步登出状态');
        handleAuthExpired();
      }
    };

    // 监听token无效事件
    const handleTokenInvalid = () => {
      console.warn('Token无效，清除认证状态');
      handleAuthExpired();
    };

    window.addEventListener('auth-expired', handleAuthExpired);
    window.addEventListener('storage', handleStorageChange);
    window.addEventListener('token-invalid', handleTokenInvalid);

    return () => {
      window.removeEventListener('auth-expired', handleAuthExpired);
      window.removeEventListener('storage', handleStorageChange);
      window.removeEventListener('token-invalid', handleTokenInvalid);
    };
  }, [dispatch]);

  const handleLoginSuccess = () => {
    console.log('登录成功，更新认证状态');
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
        console.log('登录用户:', payload.username);
      } catch (error) {
        console.error('Failed to parse token after login:', error);
      }
    }
    setIsCheckingAuth(false);
  };

  // 显示加载状态
  if (isCheckingAuth) {
    return (
      <Box 
        sx={{ 
          display: 'flex', 
          flexDirection: 'column',
          justifyContent: 'center', 
          alignItems: 'center', 
          height: '100vh',
          gap: 2,
          backgroundColor: '#f5f5f5'
        }}
      >
        <CircularProgress size={60} />
        <Typography variant="body1" color="text.secondary" sx={{ mt: 2 }}>
          正在验证登录状态...
        </Typography>
        <Typography variant="body2" color="text.disabled">
          请稍候片刻
        </Typography>
      </Box>
    );
  }

  // 未认证时显示登录页面
  if (!isAuthenticated) {
    return <LoginPage onLoginSuccess={handleLoginSuccess} />;
  }

  // 已认证时显示主界面
  return <MainLayout />;
};

export default AuthGuard;
