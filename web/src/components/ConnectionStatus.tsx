import { Chip, Box } from '@mui/material';
import { CheckCircle, Error, Pending } from '@mui/icons-material';
import { useApp } from '../hooks/useApp';

const ConnectionStatus = () => {
  const { state } = useApp();

  const getStatusConfig = () => {
    if (state.isLoading) {
      return {
        label: '连接中...',
        color: 'default' as const,
        icon: <Pending />,
      };
    }
    
    if (state.isConnected && state.health?.agent_initialized) {
      // 检查自然语言处理是否可用
      const nlpEnabled = state.health?.natural_language_enabled !== false;
      return {
        label: nlpEnabled ? '已连接' : '部分功能不可用',
        color: nlpEnabled ? 'success' as const : 'warning' as const,
        icon: <CheckCircle />,
      };
    }
    
    return {
      label: '连接失败',
      color: 'error' as const,
      icon: <Error />,
    };
  };

  const { label, color, icon } = getStatusConfig();

  return (
    <Box>
      <Chip
        label={label}
        color={color}
        icon={icon}
        variant="outlined"
        size="small"
      />
    </Box>
  );
};

export default ConnectionStatus;
