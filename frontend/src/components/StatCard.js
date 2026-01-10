import React from 'react';
import {Statistic} from 'antd';
import GlassCard from './GlassCard';
import {glacierTheme} from '../styles/theme';

/**
 * 统计卡片组件
 */
const StatCard = ({title, value, icon, color, ...props}) => {
  const colorMap = {
    primary: glacierTheme.colors.primary,
    success: glacierTheme.colors.success,
    warning: glacierTheme.colors.warning,
    info: glacierTheme.colors.info,
  };

  const cardColor = colorMap[color] || glacierTheme.colors.primary;

  return (
    <GlassCard
      hoverable
      style={{
        textAlign: 'center',
        ...props.style,
      }}
    >
      {icon && (
        <div style={{
          fontSize: '32px',
          marginBottom: glacierTheme.spacing.md,
          color: cardColor,
        }}>
          {icon}
        </div>
      )}
      <Statistic
        title={<span style={{color: glacierTheme.colors.textSecondary, fontSize: '14px'}}>{title}</span>}
        value={value}
        valueStyle={{
          color: cardColor,
          fontSize: '28px',
          fontWeight: 600,
        }}
      />
    </GlassCard>
  );
};

export default StatCard;
