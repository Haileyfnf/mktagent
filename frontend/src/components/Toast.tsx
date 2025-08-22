import React, { useEffect } from 'react';

interface ToastProps {
  message: string;
  type: 'success' | 'error' | 'info';
  onClose: () => void;
}

const Toast: React.FC<ToastProps> = ({ message, type, onClose }) => {
  useEffect(() => {
    const timer = setTimeout(() => {
      onClose();
    }, 3000);

    return () => clearTimeout(timer);
  }, [onClose]);

  const getToastStyle = () => {
    const baseStyle = {
      position: 'fixed' as const,
      top: '20px',
      right: '20px',
      padding: '12px 20px',
      borderRadius: '6px',
      color: 'white',
      fontSize: '14px',
      fontWeight: '500',
      zIndex: 1000,
      boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
      cursor: 'pointer',
      minWidth: '200px',
      maxWidth: '400px',
      wordBreak: 'break-word' as const,
      transform: 'translateX(0)',
      opacity: 1,
      transition: 'all 0.3s ease-out',
    };

    switch (type) {
      case 'success':
        return { ...baseStyle, backgroundColor: '#52c41a' };
      case 'error':
        return { ...baseStyle, backgroundColor: '#ff4d4f' };
      case 'info':
        return { ...baseStyle, backgroundColor: '#1890ff' };
      default:
        return { ...baseStyle, backgroundColor: '#1890ff' };
    }
  };

  return (
    <div style={getToastStyle()} onClick={onClose}>
      {message}
    </div>
  );
};

export default Toast; 