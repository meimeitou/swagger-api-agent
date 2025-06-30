import { useState, useEffect } from 'react';
import {
  Box,
  AppBar,
  Toolbar,
  Typography,
  Paper,
  Alert,
  Snackbar,
} from '@mui/material';
import { useApp } from '../hooks/useApp';
import ConnectionStatus from './ConnectionStatus';
import ChatInterface from './ChatInterface';
import FunctionsList from './FunctionsList';
import ApiInfo from './ApiInfo';
import apiService from '../services/api';

const MainLayout = () => {
  const { state, dispatch } = useApp();
  const [snackbarOpen, setSnackbarOpen] = useState(false);

  // 初始化连接检查
  useEffect(() => {
    const checkConnection = async () => {
      dispatch({ type: 'SET_LOADING', payload: true });
      try {
        console.log('开始连接检查...');
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
        dispatch({ type: 'SET_ERROR', payload: '无法连接到后端服务' });
        setSnackbarOpen(true);
      } finally {
        dispatch({ type: 'SET_LOADING', payload: false });
      }
    };

    checkConnection();
  }, [dispatch]);

  const handleCloseSnackbar = () => {
    setSnackbarOpen(false);
    dispatch({ type: 'CLEAR_ERROR' });
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
          <ConnectionStatus />
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
          {/* 左侧面板 - API信息和函数列表 */}
          <Box sx={{ 
            flex: '1', 
            width: { xs: '100%', md: '40%' }, // 在桌面端占40%宽度
            minWidth: '350px',
            maxWidth: '500px',
            height: '100%' // 填满容器高度
          }}>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, height: '100%' }}>
              <Paper sx={{ p: 2, flexShrink: 0 }}>
                <ApiInfo />
              </Paper>
              <Paper sx={{ 
                p: 2, 
                flexGrow: 1, 
                overflow: 'auto',
                minHeight: 0 // 确保flex子项能正确缩放
              }}>
                <FunctionsList />
              </Paper>
            </Box>
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
