import React from 'react';
import {Button} from 'antd';
import {glacierTheme} from '../styles/theme';

/**
 * 带动画效果的按钮组件
 */
const AnimatedButton = ({
                          children,
                          type = 'default',
                          style = {},
                          className = '',
                          ...props
                        }) => {
  const getButtonStyle = () => {
    const baseStyle = {
      borderRadius: glacierTheme.borderRadius.md,
      transition: `all ${glacierTheme.transitions.spring}`,
      fontWeight: 500,
      border: 'none',
      ...style,
    };

    switch (type) {
      case 'primary':
        return {
          ...baseStyle,
          background: `linear-gradient(135deg, ${glacierTheme.colors.primary} 0%, ${glacierTheme.colors.primaryDark} 100%)`,
          color: '#fff',
          boxShadow: glacierTheme.shadows.md,
        };
      case 'secondary':
        return {
          ...baseStyle,
          background: `linear-gradient(135deg, ${glacierTheme.colors.secondary} 0%, ${glacierTheme.colors.secondaryDark} 100%)`,
          color: '#fff',
          boxShadow: glacierTheme.shadows.md,
        };
      default:
        return {
          ...baseStyle,
          background: glacierTheme.colors.surface,
          color: glacierTheme.colors.text,
          boxShadow: glacierTheme.shadows.sm,
        };
    }
  };

  return (
    <Button
      {...props}
      type={type === 'primary' || type === 'secondary' ? 'default' : type}
      className={className}
      style={getButtonStyle()}
      onMouseEnter={(e) => {
        e.currentTarget.style.transform = 'scale(1.05)';
        e.currentTarget.style.boxShadow = glacierTheme.shadows.lg;
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.transform = 'scale(1)';
        e.currentTarget.style.boxShadow = getButtonStyle().boxShadow;
      }}
      onMouseDown={(e) => {
        e.currentTarget.style.transform = 'scale(0.98)';
      }}
      onMouseUp={(e) => {
        e.currentTarget.style.transform = 'scale(1.05)';
      }}
    >
      {children}
    </Button>
  );
};

export default AnimatedButton;
