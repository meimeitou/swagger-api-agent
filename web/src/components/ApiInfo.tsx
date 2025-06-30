import { Typography, Box, Divider, List, ListItem, ListItemText } from '@mui/material';
import { useApp } from '../hooks/useApp';

const ApiInfo = () => {
  const { state } = useApp();

  if (!state.health) {
    return (
      <Box>
        <Typography variant="h6" gutterBottom>
          API 信息
        </Typography>
        <Typography variant="body2" color="text.secondary">
          暂无连接信息
        </Typography>
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        API 信息
      </Typography>
      <Divider sx={{ mb: 2 }} />
      
      <List dense>
        <ListItem disablePadding>
          <ListItemText
            primary="连接状态"
            secondary={state.health.status || 'Unknown'}
          />
        </ListItem>
        
        {state.health.api_title && (
          <ListItem disablePadding>
            <ListItemText
              primary="API 名称"
              secondary={state.health.api_title}
            />
          </ListItem>
        )}
        
        {state.health.api_version && (
          <ListItem disablePadding>
            <ListItemText
              primary="API 版本"
              secondary={state.health.api_version}
            />
          </ListItem>
        )}
        
        {state.health.endpoints_count !== undefined && (
          <ListItem disablePadding>
            <ListItemText
              primary="端点数量"
              secondary={state.health.endpoints_count}
            />
          </ListItem>
        )}
        
        <ListItem disablePadding>
          <ListItemText
            primary="Agent 状态"
            secondary={state.health.agent_initialized ? '已初始化' : '未初始化'}
          />
        </ListItem>
        
        {state.health.timestamp && (
          <ListItem disablePadding>
            <ListItemText
              primary="最后更新"
              secondary={new Date(state.health.timestamp).toLocaleString()}
            />
          </ListItem>
        )}
      </List>
    </Box>
  );
};

export default ApiInfo;
