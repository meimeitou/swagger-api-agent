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
      return {
        label: '已连接',
        color: 'success' as const,
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
