import { useState } from 'react';
import {
  Typography,
  Box,
  Divider,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  Collapse,
  TextField,
  InputAdornment,
  Chip,
} from '@mui/material';
import { Search, ExpandLess, ExpandMore, Functions } from '@mui/icons-material';
import { useApp } from '../hooks/useApp';

const FunctionsList = () => {
  const { state } = useApp();
  const [searchTerm, setSearchTerm] = useState('');
  const [expandedItem, setExpandedItem] = useState<string | null>(null);

  const filteredFunctions = state.functions.filter(func =>
    func.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (func.description && func.description.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  const handleItemClick = (functionName: string) => {
    setExpandedItem(expandedItem === functionName ? null : functionName);
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
        <Functions sx={{ mr: 1 }} />
        <Typography variant="h6">
          可用函数
        </Typography>
        <Chip 
          label={filteredFunctions.length} 
          size="small" 
          sx={{ ml: 1 }} 
        />
      </Box>
      
      <TextField
        fullWidth
        size="small"
        placeholder="搜索函数..."
        value={searchTerm}
        onChange={(e) => setSearchTerm(e.target.value)}
        InputProps={{
          startAdornment: (
            <InputAdornment position="start">
              <Search />
            </InputAdornment>
          ),
        }}
        sx={{ mb: 2 }}
      />
      
      <Divider sx={{ mb: 1 }} />
      
      {filteredFunctions.length === 0 ? (
        <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', py: 2 }}>
          {state.functions.length === 0 ? '暂无可用函数' : '未找到匹配的函数'}
        </Typography>
      ) : (
        <List dense>
          {filteredFunctions.map((func) => (
            <Box key={func.name}>
              <ListItem disablePadding>
                <ListItemButton
                  onClick={() => handleItemClick(func.name)}
                  sx={{ py: 0.5 }}
                >
                  <ListItemText
                    primary={func.name}
                    secondary={func.description}
                    primaryTypographyProps={{ 
                      fontSize: '0.9rem',
                      fontWeight: 'medium' 
                    }}
                    secondaryTypographyProps={{ 
                      fontSize: '0.8rem',
                      noWrap: expandedItem !== func.name 
                    }}
                  />
                  {expandedItem === func.name ? <ExpandLess /> : <ExpandMore />}
                </ListItemButton>
              </ListItem>
              
              <Collapse in={expandedItem === func.name} timeout="auto" unmountOnExit>
                <Box sx={{ pl: 2, pr: 1, pb: 1 }}>
                  {func.description && (
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                      {func.description}
                    </Typography>
                  )}
                  
                  {func.parameters && Object.keys(func.parameters).length > 0 && (
                    <Box sx={{ mb: 1 }}>
                      <Typography variant="caption" fontWeight="bold">
                        参数:
                      </Typography>
                      <Box component="pre" sx={{ 
                        fontSize: '0.7rem',
                        backgroundColor: 'grey.100',
                        p: 1,
                        borderRadius: 1,
                        overflow: 'auto',
                        maxHeight: '100px'
                      }}>
                        {JSON.stringify(func.parameters, null, 2)}
                      </Box>
                    </Box>
                  )}
                  
                  <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
                    <Chip
                      label="使用此函数"
                      size="small"
                      disabled
                      sx={{ fontSize: '0.7rem' }}
                    />
                  </Box>
                </Box>
              </Collapse>
            </Box>
          ))}
        </List>
      )}
    </Box>
  );
};

export default FunctionsList;
