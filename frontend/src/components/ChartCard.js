import React from 'react';
import {Column, Pie, Line, Area, ColumnConfig, PieConfig, LineConfig, AreaConfig} from '@ant-design/charts';
import GlassCard from './GlassCard';
import {glacierTheme} from '../styles/theme';

/**
 * 通用图表卡片组件
 */
const ChartCard = ({title, chartType, data, config = {}, style, ...props}) => {
  const baseConfig = {
    theme: {
      color10: [
        glacierTheme.colors.primary,
        glacierTheme.colors.secondary,
        glacierTheme.colors.success,
        glacierTheme.colors.warning,
        glacierTheme.colors.info,
        glacierTheme.colors.error,
        '#52c41a',
        '#faad14',
        '#1890ff',
        '#722ed1',
      ],
    },
    padding: [20, 20, 40, 60],
    ...config,
  };

  const renderChart = () => {
    switch (chartType) {
      case 'column':
        return <Column data={data} {...baseConfig}/>;
      case 'pie':
        return <Pie data={data} {...baseConfig}/>;
      case 'line':
        return <Line data={data} {...baseConfig}/>;
      case 'area':
        return <Area data={data} {...baseConfig}/>;
      default:
        return <Column data={data} {...baseConfig}/>;
    }
  };

  return (
    <GlassCard
      style={{
        padding: glacierTheme.spacing.lg,
        ...style,
      }}
      {...props}
    >
      {title && (
        <div style={{
          marginBottom: glacierTheme.spacing.md,
          fontSize: '16px',
          fontWeight: 600,
          color: glacierTheme.colors.text,
        }}>
          {title}
        </div>
      )}
      <div style={{minHeight: '300px'}}>
        {renderChart()}
      </div>
    </GlassCard>
  );
};

export default ChartCard;
