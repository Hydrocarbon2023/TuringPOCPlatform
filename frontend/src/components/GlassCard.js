import React, {useState} from 'react';
import {Card} from 'antd';
import {glacierTheme} from '../styles/theme';

/**
 * 毛玻璃卡片组件
 * 带有冰川蓝与火烈鸟红色系和弥散阴影效果
 */
const GlassCard = ({
                     children,
                     hoverable = false,
                     onClick,
                     style = {},
                     className = '',
                     ...props
                   }) => {
  const [isHovered, setIsHovered] = useState(false);

  const baseStyle = {
    ...glacierTheme.glass,
    borderRadius: glacierTheme.borderRadius.lg,
    transition: `all ${glacierTheme.transitions.normal}`,
    border: glacierTheme.glass.border,
    boxShadow: isHovered && (hoverable || onClick)
      ? glacierTheme.shadows.glassHover
      : glacierTheme.shadows.glass,
    background: isHovered && (hoverable || onClick)
      ? 'rgba(255, 255, 255, 0.8)'
      : glacierTheme.glass.background,
    transform: isHovered && (hoverable || onClick) ? 'translateY(-4px)' : 'translateY(0)',
    cursor: (hoverable || onClick) ? 'pointer' : 'default',
    ...style,
  };

  return (
    <Card
      {...props}
      className={className}
      style={baseStyle}
      bodyStyle={{
        padding: glacierTheme.spacing.lg,
        ...props.bodyStyle,
      }}
      onClick={onClick}
      onMouseEnter={() => {
        if (hoverable || onClick) {
          setIsHovered(true);
        }
      }}
      onMouseLeave={() => {
        if (hoverable || onClick) {
          setIsHovered(false);
        }
      }}
    >
      {children}
    </Card>
  );
};

export default GlassCard;
