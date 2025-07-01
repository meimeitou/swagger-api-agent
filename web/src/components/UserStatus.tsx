import { Box, Typography, Avatar, Tooltip } from '@mui/material';
import { useApp } from '../hooks/useApp';
import AccountCircleIcon from '@mui/icons-material/AccountCircle';

const UserStatus = () => {
  const { state } = useApp();
  const { isAuthenticated, userInfo, isConnected } = state;

  if (!isAuthenticated || !userInfo) {
    return null;
  }

  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
      <Tooltip title={`登录时间: ${userInfo.loginTime}`}> 
        <Avatar sx={{ width: 28, height: 28, bgcolor: isConnected ? 'success.main' : 'grey.500' }}>
          <AccountCircleIcon />
        </Avatar>
      </Tooltip>
      <Typography variant="body2" sx={{ color: isConnected ? 'success.main' : 'text.secondary', fontWeight: 500 }}>
        {userInfo.username}
      </Typography>
    </Box>
  );
};

export default UserStatus;
