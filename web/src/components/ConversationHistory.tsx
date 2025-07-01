import { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  List,
  ListItem,
  ListItemText,
  ListItemAvatar,
  Avatar,
  IconButton,
  Tooltip,
  Divider,
  Alert,
  Chip,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  CircularProgress,
} from '@mui/material';
import {
  Person,
  Delete,
  Refresh,
  History,
  Warning,
} from '@mui/icons-material';
import { useApp } from '../hooks/useApp';
import apiService from '../services/api';
import type { ConversationMessage } from '../services/api';

const ConversationHistory = () => {
  const { state, dispatch } = useApp();
  const [isLoading, setIsLoading] = useState(false);
  const [clearDialogOpen, setClearDialogOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 刷新对话历史
  const handleRefreshHistory = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await apiService.getConversationHistory();
      if (response.success && response.data) {
        dispatch({ type: 'SET_CONVERSATIONS', payload: response.data });
      } else {
        setError(response.error || '获取对话历史失败');
      }
    } catch (error) {
      console.error('Failed to refresh history:', error);
      setError('获取对话历史失败');
    } finally {
      setIsLoading(false);
    }
  };

  // 清空对话历史
  const handleClearHistory = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await apiService.clearConversationHistory();
      if (response.success) {
        dispatch({ type: 'SET_CONVERSATIONS', payload: [] });
        setClearDialogOpen(false);
      } else {
        setError(response.error || '清空历史失败');
      }
    } catch (error) {
      console.error('Failed to clear history:', error);
      setError('清空历史失败');
    } finally {
      setIsLoading(false);
    }
  };

  // 格式化时间戳
  const formatTimestamp = (timestamp: string) => {
    try {
      const date = new Date(timestamp);
      return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
      });
    } catch {
      return timestamp;
    }
  };

  // 组件挂载时加载历史记录
  useEffect(() => {
    const loadHistory = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const response = await apiService.getConversationHistory();
        if (response.success && response.data) {
          dispatch({ type: 'SET_CONVERSATIONS', payload: response.data });
        } else {
          setError(response.error || '获取对话历史失败');
        }
      } catch (error) {
        console.error('Failed to load history:', error);
        setError('获取对话历史失败');
      } finally {
        setIsLoading(false);
      }
    };
    
    loadHistory();
  }, [dispatch]);

  const { conversations } = state;

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* 标题和操作按钮 */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <History />
          用户请求历史
          <Chip 
            label={conversations.filter(msg => msg.role === 'user').length} 
            size="small" 
            color="primary" 
            variant="outlined" 
          />
        </Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Tooltip title="刷新历史">
            <IconButton onClick={handleRefreshHistory} disabled={isLoading} size="small">
              <Refresh />
            </IconButton>
          </Tooltip>
          <Tooltip title="清空历史">
            <IconButton 
              onClick={() => setClearDialogOpen(true)} 
              disabled={isLoading || conversations.filter(msg => msg.role === 'user').length === 0}
              size="small"
              color="error"
            >
              <Delete />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {/* 错误提示 */}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* 加载状态 */}
      {isLoading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 2 }}>
          <CircularProgress size={24} />
        </Box>
      )}

      {/* 对话列表 - 只显示用户请求 */}
      <Paper sx={{ flexGrow: 1, overflow: 'auto' }} variant="outlined">
        {conversations.filter(msg => msg.role === 'user').length === 0 ? (
          <Box sx={{ p: 3, textAlign: 'center', color: 'text.secondary' }}>
            <History sx={{ fontSize: 48, opacity: 0.5, mb: 1 }} />
            <Typography>暂无用户请求历史</Typography>
          </Box>
        ) : (
          <List sx={{ p: 0 }}>
            {conversations
              .filter(message => message.role === 'user')
              .map((message: ConversationMessage, index: number) => (
              <Box key={index}>
                <ListItem alignItems="flex-start" sx={{ py: 1.5 }}>
                  <ListItemAvatar>
                    <Avatar 
                      sx={{ 
                        bgcolor: 'primary.main',
                        width: 32, 
                        height: 32 
                      }}
                    >
                      <Person />
                    </Avatar>
                  </ListItemAvatar>
                  <ListItemText
                    primary={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                        <Chip 
                          label="用户请求" 
                          size="small" 
                          color="primary"
                          variant="outlined"
                        />
                        <Typography variant="caption" color="text.secondary">
                          {formatTimestamp(message.timestamp)}
                        </Typography>
                      </Box>
                    }
                    secondary={
                      <Typography 
                        component="div" 
                        variant="body2" 
                        sx={{ 
                          mt: 0.5,
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          whiteSpace: 'nowrap',
                          maxWidth: '100%'
                        }}
                        title={message.content} // 鼠标悬停显示完整内容
                      >
                        {message.content}
                      </Typography>
                    }
                  />
                </ListItem>
                {index < conversations.filter(msg => msg.role === 'user').length - 1 && <Divider />}
              </Box>
            ))}
          </List>
        )}
      </Paper>

      {/* 清空确认对话框 */}
      <Dialog open={clearDialogOpen} onClose={() => setClearDialogOpen(false)}>
        <DialogTitle sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Warning color="warning" />
          确认清空用户请求历史
        </DialogTitle>
        <DialogContent>
          <Typography>
            确定要清空所有用户请求历史吗？此操作不可撤销。
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setClearDialogOpen(false)}>
            取消
          </Button>
          <Button 
            onClick={handleClearHistory} 
            color="error" 
            disabled={isLoading}
            startIcon={isLoading ? <CircularProgress size={16} /> : <Delete />}
          >
            确认清空
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ConversationHistory;
