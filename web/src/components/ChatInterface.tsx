import { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';
import 'highlight.js/styles/github.css'; // 代码高亮样式
import {
  Box,
  TextField,
  Button,
  Typography,
  Paper,
  List,
  ListItem,
  Avatar,
  Divider,
  CircularProgress,
  Alert,
  IconButton,
  Tooltip,
  Collapse,
  Chip,
} from '@mui/material';
import {
  Send,
  Person,
  SmartToy,
  Clear,
  Refresh,
  ExpandMore,
  ExpandLess,
  ContentCopy,
} from '@mui/icons-material';
import { useApp } from '../hooks/useApp';
import apiService from '../services/api';

const ChatInterface = () => {
  const { state, dispatch } = useApp();
  const [inputMessage, setInputMessage] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [expandedMessages, setExpandedMessages] = useState<Set<number>>(new Set());
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [state.conversations]);

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isProcessing || !state.isConnected) {
      return;
    }

    const userMessage = inputMessage.trim();
    setInputMessage('');
    setIsProcessing(true);

    // 添加用户消息到对话历史
    const userConversation = {
      role: 'user',
      content: userMessage,
      timestamp: new Date().toISOString(),
    };
    dispatch({ type: 'ADD_CONVERSATION', payload: userConversation });

    try {
      // 调用API处理自然语言
      const response = await apiService.processNaturalLanguage({
        message: userMessage,
        context: {},
      });

      // 添加AI回复到对话历史
      let aiContent = '';
      if (response.success) {
        // 优先使用 message 字段，它包含完整的处理结果描述
        if (response.message) {
          aiContent = response.message;
        } else if (response.data) {
          // 如果没有 message，则格式化显示 data
          aiContent = JSON.stringify(response.data, null, 2);
        } else {
          aiContent = '处理成功';
        }
      } else {
        aiContent = response.error || '处理失败';
      }

      const aiConversation = {
        role: 'assistant',
        content: aiContent,
        timestamp: new Date().toISOString(),
      };
      dispatch({ type: 'ADD_CONVERSATION', payload: aiConversation });

      if (!response.success) {
        dispatch({ type: 'SET_ERROR', payload: response.error || '处理失败' });
      }

    } catch (error) {
      console.error('Failed to process message:', error);
      const errorConversation = {
        role: 'assistant',
        content: '抱歉，处理您的请求时发生错误。请检查网络连接或稍后重试。',
        timestamp: new Date().toISOString(),
      };
      dispatch({ type: 'ADD_CONVERSATION', payload: errorConversation });
      dispatch({ type: 'SET_ERROR', payload: '发送消息失败' });
    } finally {
      setIsProcessing(false);
    }
  };

  const handleKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSendMessage();
    }
  };

  const handleClearHistory = async () => {
    try {
      const response = await apiService.clearConversationHistory();
      if (response.success) {
        dispatch({ type: 'SET_CONVERSATIONS', payload: [] });
      } else {
        dispatch({ type: 'SET_ERROR', payload: response.error || '清空历史失败' });
      }
    } catch (error) {
      console.error('Failed to clear history:', error);
      dispatch({ type: 'SET_ERROR', payload: '清空历史失败' });
    }
  };

  const handleRefreshHistory = async () => {
    try {
      const response = await apiService.getConversationHistory();
      if (response.success && response.data) {
        dispatch({ type: 'SET_CONVERSATIONS', payload: response.data });
      }
    } catch (error) {
      console.error('Failed to refresh history:', error);
    }
  };

  const formatMessageContent = (content: string) => {
    try {
      // 尝试解析JSON并格式化显示
      const parsed = JSON.parse(content);
      return JSON.stringify(parsed, null, 2);
    } catch {
      // 如果不是JSON，直接返回原内容
      return content;
    }
  };

  const isMarkdownContent = (content: string) => {
    // 检查常见的 Markdown 语法特征
    const markdownPatterns = [
      /#{1,6}\s+/, // 标题
      /\*\*.*\*\*/, // 粗体
      /\*.*\*/, // 斜体
      /```[\s\S]*```/, // 代码块
      /`.*`/, // 内联代码
      /^\s*[-*+]\s+/m, // 列表
      /^\s*\d+\.\s+/m, // 有序列表
      /\[.*\]\(.*\)/, // 链接
      /!\[.*\]\(.*\)/, // 图片
      /^\s*>\s+/m, // 引用
    ];
    
    return markdownPatterns.some(pattern => pattern.test(content));
  };

  const isJSONContent = (content: string) => {
    return content.trim().startsWith('{') || content.trim().startsWith('[');
  };

  const isLongContent = (content: string) => {
    return content.length > 500 || content.split('\n').length > 10;
  };

  const toggleMessageExpansion = (index: number) => {
    const newExpanded = new Set(expandedMessages);
    if (newExpanded.has(index)) {
      newExpanded.delete(index);
    } else {
      newExpanded.add(index);
    }
    setExpandedMessages(newExpanded);
  };

  const copyToClipboard = async (content: string) => {
    try {
      await navigator.clipboard.writeText(content);
      // 这里可以添加复制成功的提示
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  // 渲染消息内容的组件
  const renderMessageContent = (content: string) => {
    const isJSON = isJSONContent(content);
    const isMarkdown = isMarkdownContent(content);

    if (isJSON) {
      // JSON 内容使用代码样式显示
      return (
        <Typography 
          variant="body2" 
          component="pre"
          sx={{ 
            whiteSpace: 'pre-wrap',
            wordBreak: 'break-word',
            fontFamily: 'monospace',
            fontSize: '0.8rem',
            overflow: 'visible',
            textOverflow: 'unset',
            display: 'block',
            width: '100%',
            maxWidth: 'none',
            lineHeight: 1.5
          }}
        >
          {formatMessageContent(content)}
        </Typography>
      );
    } else if (isMarkdown) {
      // Markdown 内容使用 ReactMarkdown 渲染
      return (
        <Box sx={{ 
          '& h1, & h2, & h3, & h4, & h5, & h6': {
            marginTop: '16px',
            marginBottom: '8px',
            fontWeight: 'bold'
          },
          '& h1': { fontSize: '1.5rem' },
          '& h2': { fontSize: '1.3rem' },
          '& h3': { fontSize: '1.1rem' },
          '& p': {
            marginBottom: '8px',
            lineHeight: 1.6
          },
          '& code': {
            backgroundColor: 'rgba(0, 0, 0, 0.05)',
            padding: '2px 4px',
            borderRadius: '3px',
            fontFamily: 'monospace',
            fontSize: '0.85em'
          },
          '& pre': {
            backgroundColor: 'rgba(0, 0, 0, 0.05)',
            padding: '12px',
            borderRadius: '6px',
            overflow: 'auto',
            marginBottom: '8px'
          },
          '& blockquote': {
            borderLeft: '4px solid #ddd',
            paddingLeft: '16px',
            marginLeft: '0',
            marginBottom: '8px',
            fontStyle: 'italic'
          },
          '& ul, & ol': {
            paddingLeft: '20px',
            marginBottom: '8px'
          },
          '& li': {
            marginBottom: '4px'
          },
          '& table': {
            borderCollapse: 'collapse',
            marginBottom: '8px',
            width: '100%'
          },
          '& th, & td': {
            border: '1px solid #ddd',
            padding: '8px',
            textAlign: 'left'
          },
          '& th': {
            backgroundColor: 'rgba(0, 0, 0, 0.05)',
            fontWeight: 'bold'
          }
        }}>
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            rehypePlugins={[rehypeHighlight]}
          >
            {content}
          </ReactMarkdown>
        </Box>
      );
    } else {
      // 普通文本内容
      return (
        <Typography 
          variant="body2" 
          component="pre"
          sx={{ 
            whiteSpace: 'pre-wrap',
            wordBreak: 'break-word',
            fontFamily: 'inherit',
            fontSize: 'inherit',
            overflow: 'visible',
            textOverflow: 'unset',
            display: 'block',
            width: '100%',
            maxWidth: 'none',
            lineHeight: 1.5
          }}
        >
          {content}
        </Typography>
      );
    }
  };

  return (
    <Box sx={{ 
      height: '100%', 
      display: 'flex', 
      flexDirection: 'column',
      minHeight: 0 // 确保flex容器能正确缩放
    }}>
      {/* 头部工具栏 */}
      <Box sx={{ 
        display: 'flex', 
        alignItems: 'center', 
        mb: 1.5,
        flexShrink: 0 // 防止头部被压缩
      }}>
        <Typography variant="h6" sx={{ flexGrow: 1 }}>
          智能对话
        </Typography>
        <Tooltip title="刷新历史">
          <IconButton onClick={handleRefreshHistory} size="small">
            <Refresh />
          </IconButton>
        </Tooltip>
        <Tooltip title="清空历史">
          <IconButton onClick={handleClearHistory} size="small">
            <Clear />
          </IconButton>
        </Tooltip>
      </Box>

      <Divider sx={{ mb: 1.5, flexShrink: 0 }} />

      {/* 连接状态提示 */}
      {!state.isConnected && (
        <Alert severity="warning" sx={{ mb: 1.5, flexShrink: 0 }}>
          未连接到后端服务，请检查服务状态
        </Alert>
      )}

      {/* 消息列表 */}
      <Box sx={{ 
        flexGrow: 1, 
        overflow: 'auto', 
        mb: 1.5,
        border: '1px solid',
        borderColor: 'divider',
        borderRadius: 1,
        p: 1,
        width: '100%',
        minHeight: 0,
        maxHeight: '100%'
      }}>
        {state.conversations.length === 0 ? (
          <Box sx={{ 
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'center', 
            height: '100%',
            color: 'text.secondary'
          }}>
            <Typography variant="body2">
              开始与AI助手对话，输入自然语言来调用API
            </Typography>
          </Box>
        ) : (
          <List sx={{ pt: 0 }}>
            {state.conversations.map((message, index) => (
              <ListItem key={index} sx={{ flexDirection: 'column', alignItems: 'flex-start', py: 1 }}>
                <Box sx={{ 
                  display: 'flex', 
                  alignItems: 'flex-start', 
                  width: '100%',
                  mb: 1
                }}>
                  <Avatar sx={{ 
                    mr: 2, 
                    bgcolor: message.role === 'user' ? 'primary.main' : 'secondary.main',
                    width: 32,
                    height: 32,
                  }}>
                    {message.role === 'user' ? <Person /> : <SmartToy />}
                  </Avatar>
                  <Box sx={{ flexGrow: 1, width: '100%', minWidth: 0 }}>
                    <Typography variant="caption" color="text.secondary">
                      {message.role === 'user' ? '您' : 'AI助手'} • {new Date(message.timestamp).toLocaleTimeString()}
                    </Typography>
                    <Paper sx={{ 
                      p: 2, 
                      mt: 0.5,
                      backgroundColor: message.role === 'user' ? 'primary.50' : 'grey.50',
                      width: '100%',
                      overflow: 'visible',
                      position: 'relative'
                    }}>
                      {/* 消息操作按钮 */}
                      <Box sx={{ 
                        position: 'absolute', 
                        top: 8, 
                        right: 8,
                        display: 'flex',
                        gap: 0.5
                      }}>
                        {isLongContent(message.content) && (
                          <Tooltip title={expandedMessages.has(index) ? "收起" : "展开"}>
                            <IconButton 
                              size="small" 
                              onClick={() => toggleMessageExpansion(index)}
                              sx={{ bgcolor: 'background.paper', '&:hover': { bgcolor: 'grey.200' } }}
                            >
                              {expandedMessages.has(index) ? <ExpandLess /> : <ExpandMore />}
                            </IconButton>
                          </Tooltip>
                        )}
                        <Tooltip title="复制内容">
                          <IconButton 
                            size="small" 
                            onClick={() => copyToClipboard(message.content)}
                            sx={{ bgcolor: 'background.paper', '&:hover': { bgcolor: 'grey.200' } }}
                          >
                            <ContentCopy />
                          </IconButton>
                        </Tooltip>
                      </Box>

                      {/* 消息内容 */}
                      <Box sx={{ pr: 6 }}> {/* 给右侧按钮留出空间 */}
                        {isLongContent(message.content) ? (
                          <Collapse 
                            in={expandedMessages.has(index)} 
                            collapsedSize="300px"
                            timeout="auto"
                          >
                            {renderMessageContent(message.content)}
                          </Collapse>
                        ) : (
                          renderMessageContent(message.content)
                        )}

                        {/* 内容长度提示 */}
                        {isLongContent(message.content) && !expandedMessages.has(index) && (
                          <Box sx={{ 
                            position: 'absolute',
                            bottom: 8,
                            left: 16,
                            right: 50
                          }}>
                            <Box sx={{
                              background: 'linear-gradient(transparent, rgba(255,255,255,0.8))',
                              height: '20px',
                              display: 'flex',
                              alignItems: 'end',
                              justifyContent: 'center'
                            }}>
                              <Chip 
                                label={`${message.content.length} 字符`}
                                size="small"
                                variant="outlined"
                                sx={{ fontSize: '0.7rem' }}
                              />
                            </Box>
                          </Box>
                        )}
                      </Box>
                    </Paper>
                  </Box>
                </Box>
              </ListItem>
            ))}
            {isProcessing && (
              <ListItem sx={{ justifyContent: 'center' }}>
                <CircularProgress size={24} />
                <Typography variant="body2" sx={{ ml: 2 }}>
                  AI正在处理中...
                </Typography>
              </ListItem>
            )}
          </List>
        )}
        <div ref={messagesEndRef} />
      </Box>

      {/* LLM 状态提示 */}
      {state.isConnected && state.health?.natural_language_enabled === false && (
        <Alert severity="warning" sx={{ mb: 2 }}>
          自然语言处理服务暂时不可用，您可以通过"函数列表"标签页直接调用 API 接口
        </Alert>
      )}

      {/* 输入区域 */}
      <Box sx={{ 
        display: 'flex', 
        gap: 1,
        flexShrink: 0 // 防止输入区域被压缩
      }}>
        <TextField
          fullWidth
          multiline
          maxRows={4}
          placeholder={
            state.health?.natural_language_enabled === false 
              ? "自然语言处理服务暂不可用，请使用函数列表"
              : "输入您的问题或需求..."
          }
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          onKeyPress={handleKeyPress}
          disabled={!state.isConnected || isProcessing || state.health?.natural_language_enabled === false}
          variant="outlined"
          size="small"
        />
        <Button
          variant="contained"
          onClick={handleSendMessage}
          disabled={
            !inputMessage.trim() || 
            !state.isConnected || 
            isProcessing || 
            state.health?.natural_language_enabled === false
          }
          sx={{ minWidth: 'auto', px: 2 }}
        >
          {isProcessing ? <CircularProgress size={20} /> : <Send />}
        </Button>
      </Box>
    </Box>
  );
};

export default ChatInterface;
