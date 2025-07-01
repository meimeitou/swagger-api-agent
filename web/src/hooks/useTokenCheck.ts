import { useEffect, useRef } from 'react';
import { apiService, TokenManager } from '../services/api';

/**
 * Token 自动检查 Hook
 * 定期检查token是否即将过期，并在过期前提醒用户或自动处理
 */
export const useTokenCheck = () => {
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const warningShownRef = useRef<boolean>(false);
  
  useEffect(() => {
    const checkToken = () => {
      if (!apiService.isAuthenticated()) {
        warningShownRef.current = false;
        return;
      }
      
      const token = TokenManager.getToken();
      if (!token) {
        warningShownRef.current = false;
        return;
      }
      
      try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        const exp = payload.exp * 1000; // 转换为毫秒
        const now = Date.now();
        const timeUntilExpiry = exp - now;
        
        // 如果token在5分钟内过期且还没有显示过警告
        if (timeUntilExpiry > 0 && timeUntilExpiry < 5 * 60 * 1000 && !warningShownRef.current) {
          console.warn('Token将在5分钟内过期，剩余时间:', Math.floor(timeUntilExpiry / 60000), '分钟');
          warningShownRef.current = true;
          
          // 触发过期警告事件
          window.dispatchEvent(new CustomEvent('token-expiring', {
            detail: { 
              timeLeft: timeUntilExpiry,
              expiryTime: new Date(exp).toLocaleString('zh-CN')
            }
          }));
        }
        
        // 如果token已过期，触发登出
        if (timeUntilExpiry <= 0) {
          console.warn('Token已过期，触发自动登出');
          warningShownRef.current = false;
          window.dispatchEvent(new CustomEvent('auth-expired'));
        }
        
        // 重置警告标志（如果距离过期还有很长时间）
        if (timeUntilExpiry > 10 * 60 * 1000) {
          warningShownRef.current = false;
        }
        
      } catch (error) {
        console.error('Token检查失败:', error);
        // Token格式错误，触发登出
        window.dispatchEvent(new CustomEvent('auth-expired'));
      }
    };
    
    // 每分钟检查一次token状态
    intervalRef.current = setInterval(checkToken, 60 * 1000);
    
    // 立即执行一次检查
    checkToken();
    
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, []);
  
  return null;
};
