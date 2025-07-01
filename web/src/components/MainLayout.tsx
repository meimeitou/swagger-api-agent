import { useState, useEffect } from 'react';
import {
  Box,
  AppBar,
  Toolbar,
  Typography,
  Paper,
  Alert,
  Snackbar,
  IconButton,
  Tooltip,
  Tabs,
  Tab,
} from '@mui/material';
import { Logout as LogoutIcon, Functions, History, Info } from '@mui/icons-material';
import { useApp } from '../hooks/useApp';
import ConnectionStatus from './ConnectionStatus';
import ChatInterface from './ChatInterface';
import FunctionsList from './FunctionsList';
import ApiInfo from './ApiInfo';
import ConversationHistory from './ConversationHistory';
import apiService from '../services/api';
import UserStatus from './UserStatus';

const MainLayout = () => {
  const { state, dispatch } = useApp();
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [leftPanelTab, setLeftPanelTab] = useState(0);
  const [tokenWarningOpen, setTokenWarningOpen] = useState(false);

  // 处理左侧面板Tab切换
  const handleLeftPanelTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setLeftPanelTab(newValue);
  };

  // 初始化连接检查
  useEffect(() => {
    const checkConnection = async () => {
      dispatch({ type: 'SET_LOADING', payload: true });
      try {
        console.log('开始连接检查...');
        
        // 先检查认证状态
        if (!apiService.isAuthenticated()) {
          console.warn('用户未认证，跳过连接检查');
          dispatch({ type: 'SET_AUTHENTICATED', payload: false });
          return;
        }
        
        const health = await apiService.healthCheck();
        console.log('健康检查成功:', health);
        dispatch({ type: 'SET_HEALTH', payload: health });
        dispatch({ type: 'SET_CONNECTED', payload: true });
        
        // 获取函数列表
        console.log('开始获取函数列表...');
        const functionsResponse = await apiService.getFunctions();
        console.log('函数列表响应:', functionsResponse);
        if (functionsResponse.success && functionsResponse.data) {
          console.log('Functions loaded:', functionsResponse.data.length);
          dispatch({ type: 'SET_FUNCTIONS', payload: functionsResponse.data });
        } else {
          console.error('Failed to load functions:', functionsResponse.error);
        }
        
        // 获取对话历史
        console.log('开始获取对话历史...');
        const historyResponse = await apiService.getConversationHistory();
        console.log('对话历史响应:', historyResponse);
        if (historyResponse.success && historyResponse.data) {
          dispatch({ type: 'SET_CONVERSATIONS', payload: historyResponse.data });
        }
        
      } catch (error) {
        console.error('Connection failed:', error);
        dispatch({ type: 'SET_CONNECTED', payload: false });
        
        // 检查是否是认证错误
        if (error && typeof error === 'object' && 'response' in error) {
          const httpError = error as { response?: { status?: number } };
          if (httpError.response?.status === 401) {
            console.warn('认证失败，用户需要重新登录');
            dispatch({ type: 'SET_AUTHENTICATED', payload: false });
            return;
          }
        }
        
        dispatch({ type: 'SET_ERROR', payload: '无法连接到后端服务' });
        setSnackbarOpen(true);
      } finally {
        dispatch({ type: 'SET_LOADING', payload: false });
      }
    };

    checkConnection();
    
    // 监听token即将过期事件
    const handleTokenExpiring = (event: CustomEvent) => {
      const { timeLeft, expiryTime } = event.detail;
      console.warn('Token即将过期:', { timeLeft, expiryTime });
      setTokenWarningOpen(true);
      dispatch({ 
        type: 'SET_ERROR', 
        payload: `登录即将过期，将在 ${Math.ceil(timeLeft / 60000)} 分钟后自动登出` 
      });
      setSnackbarOpen(true);
    };

    window.addEventListener('token-expiring', handleTokenExpiring as EventListener);

    return () => {
      window.removeEventListener('token-expiring', handleTokenExpiring as EventListener);
    };
  }, [dispatch]);

  const handleCloseSnackbar = () => {
    setSnackbarOpen(false);
    dispatch({ type: 'CLEAR_ERROR' });
  };

  const handleLogout = () => {
    apiService.logout();
    dispatch({ type: 'SET_AUTHENTICATED', payload: false });
    dispatch({ type: 'SET_USER_INFO', payload: null });
    dispatch({ type: 'SET_CONNECTED', payload: false });
    dispatch({ type: 'SET_FUNCTIONS', payload: [] });
    dispatch({ type: 'SET_CONVERSATIONS', payload: [] });
  };

  return (
    <Box sx={{ 
      width: '100vw',
      height: '100vh',
      display: 'flex',
      flexDirection: 'column',
      backgroundColor: '#f5f5f5',
      overflow: 'hidden'
    }}>
      {/* 顶部应用栏 */}
      <AppBar position="static" sx={{ width: '100%', flexShrink: 0 }}>
        <Toolbar sx={{ width: '100%' }}>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            Swagger API Agent
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <UserStatus />
            <ConnectionStatus />
            <Tooltip title="登出">
              <IconButton color="inherit" onClick={handleLogout}>
                <LogoutIcon />
              </IconButton>
            </Tooltip>
          </Box>
        </Toolbar>
      </AppBar>

      {/* 主要内容区域 */}
      <Box sx={{ 
        flexGrow: 1,
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'flex-start',
        width: '100%',
        overflow: 'hidden', // 防止内容溢出
        height: 'calc(90vh - 64px)', // 90%视口高度减去AppBar高度(约64px)
        pt: 3,
        pb: 3
      }}>
        <Box sx={{ 
          display: 'flex', 
          gap: 3, 
          flexDirection: { xs: 'column', md: 'row' },
          alignItems: 'flex-start',
          justifyContent: 'center',
          width: '80%', // 设置为屏幕宽度的80%
          maxWidth: '1400px', // 设置最大宽度限制
          height: '100%' // 填满父容器高度
        }}>
          {/* 左侧面板 - API信息、函数列表和对话历史 */}
          <Box sx={{ 
            flex: '1', 
            width: { xs: '100%', md: '40%' }, // 在桌面端占40%宽度
            minWidth: '350px',
            maxWidth: '500px',
            height: '100%' // 填满容器高度
          }}>
            <Paper sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
              {/* Tab 标签 */}
              <Tabs 
                value={leftPanelTab} 
                onChange={handleLeftPanelTabChange} 
                variant="fullWidth"
                sx={{ borderBottom: 1, borderColor: 'divider', flexShrink: 0 }}
              >
                <Tab icon={<Info />} label="API信息" />
                <Tab icon={<Functions />} label="函数列表" />
                <Tab icon={<History />} label="用户请求" />
              </Tabs>
              
              {/* Tab 内容 */}
              <Box sx={{ flexGrow: 1, overflow: 'hidden', p: 2 }}>
                {leftPanelTab === 0 && (
                  <Box sx={{ height: '100%', overflow: 'auto' }}>
                    <ApiInfo />
                  </Box>
                )}
                {leftPanelTab === 1 && (
                  <Box sx={{ height: '100%', overflow: 'auto' }}>
                    <FunctionsList />
                  </Box>
                )}
                {leftPanelTab === 2 && (
                  <Box sx={{ height: '100%' }}>
                    <ConversationHistory />
                  </Box>
                )}
              </Box>
            </Paper>
          </Box>

          {/* 右侧面板 - 聊天界面 */}
          <Box sx={{ 
            flex: '1',
            width: { xs: '100%', md: '60%' }, // 在桌面端占60%宽度
            minWidth: '400px',
            maxWidth: '800px',
            height: '100%' // 填满容器高度
          }}>
            <Paper sx={{ 
              p: 3, 
              height: '100%', // 填满父容器高度
              minHeight: '500px', 
            }}>
              <ChatInterface />
            </Paper>
          </Box>
        </Box>
      </Box>

      {/* 错误提示 */}
      <Snackbar
        open={snackbarOpen}
        autoHideDuration={6000}
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert onClose={handleCloseSnackbar} severity="error" sx={{ width: '100%' }}>
          {state.error}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default MainLayout;
