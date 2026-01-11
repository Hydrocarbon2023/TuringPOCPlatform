# 数据可视化功能实现指南

## 概述

已为整个网站添加了数据可视化功能，包括：
- 后端统计API
- 前端图表组件
- 各个Dashboard的数据可视化集成

## 已实现的功能

### 1. 后端统计API

**位置**: `backend/app.py`

#### API端点：
- `GET /api/statistics` - 全局统计数据（管理员/秘书可见）
  - 项目状态统计
  - 项目领域统计
  - 用户角色统计
  - 项目成熟度统计
  - 项目提交时间趋势
  - 经费统计
  - 孵化项目统计
  - 评审状态统计

- `GET /api/statistics/user` - 用户个人统计数据（项目负责人）
  - 我的项目状态统计
  - 我的项目领域统计
  - 我的经费统计
  - 我的里程碑统计

- `GET /api/statistics/reviewer` - 评审人统计数据
  - 评审任务状态统计
  - 评审评分统计
  - 评审项目领域统计

- `GET /api/statistics/supporter` - 企业支持者统计数据
  - 资源类型统计
  - 资源状态统计
  - 申请状态统计
  - 对接意向统计

### 2. 前端组件

#### ChartCard组件
**位置**: `frontend/src/components/ChartCard.js`

通用图表卡片组件，支持：
- Column（柱状图）
- Pie（饼图）
- Line（折线图）
- Area（面积图）

#### 使用方法：
```javascript
import ChartCard from '../../components/ChartCard';

<ChartCard
  title="项目状态分布"
  chartType="pie"
  data={[
    { type: '待初审', value: 10 },
    { type: '已通过', value: 5 },
    { type: '孵化中', value: 3 },
  ]}
  config={{
    angleField: 'value',
    colorField: 'type',
  }}
/>
```

### 3. API客户端

**位置**: `frontend/src/api/api.js`

已添加 `statisticsApi`：
```javascript
import {statisticsApi} from '../../api/api';

// 获取全局统计
const stats = await statisticsApi.getStatistics();

// 获取用户统计
const userStats = await statisticsApi.getUserStatistics();

// 获取评审人统计
const reviewerStats = await statisticsApi.getReviewerStatistics();

// 获取企业支持者统计
const supporterStats = await statisticsApi.getSupporterStatistics();
```

## 在各Dashboard中集成可视化

### AdminDashboard示例

```javascript
import React, {useState, useEffect} from 'react';
import {Row, Col} from 'antd';
import ChartCard from '../../components/ChartCard';
import {statisticsApi} from '../../api/api';

const AdminDashboard = () => {
  const [stats, setStats] = useState(null);

  useEffect(() => {
    loadStatistics();
  }, []);

  const loadStatistics = async () => {
    try {
      const res = await statisticsApi.getStatistics();
      setStats(res.data);
    } catch (e) {
      // 错误处理
    }
  };

  if (!stats) return <div>加载中...</div>;

  return (
    <div>
      {/* 项目状态分布饼图 */}
      <ChartCard
        title="项目状态分布"
        chartType="pie"
        data={stats.project_status.map(item => ({
          type: item.status,
          value: item.count,
        }))}
        config={{
          angleField: 'value',
          colorField: 'type',
        }}
      />

      {/* 项目领域柱状图 */}
      <ChartCard
        title="项目领域分布"
        chartType="column"
        data={stats.project_domain.map(item => ({
          domain: item.domain,
          count: item.count,
        }))}
        config={{
          xField: 'domain',
          yField: 'count',
        }}
      />

      {/* 项目提交趋势折线图 */}
      <ChartCard
        title="项目提交趋势（近12个月）"
        chartType="line"
        data={stats.project_trend.map(item => ({
          month: item.month,
          count: item.count,
        }))}
        config={{
          xField: 'month',
          yField: 'count',
          smooth: true,
        }}
      />
    </div>
  );
};
```

### UserDashboard示例

```javascript
import {statisticsApi} from '../../api/api';

// 在组件中添加
const [userStats, setUserStats] = useState(null);

useEffect(() => {
  loadUserStatistics();
}, []);

const loadUserStatistics = async () => {
  try {
    const res = await statisticsApi.getUserStatistics();
    setUserStats(res.data);
  } catch (e) {
    // 错误处理
  }
};

// 在Tabs中添加"数据统计"Tab
{
  key: '3',
  label: '数据统计',
  children: (
    <Row gutter={[16, 16]}>
      <Col xs={24} md={12}>
        <ChartCard
          title="我的项目状态"
          chartType="pie"
          data={userStats?.project_status.map(item => ({
            type: item.status,
            value: item.count,
          })) || []}
          config={{
            angleField: 'value',
            colorField: 'type',
          }}
        />
      </Col>
      <Col xs={24} md={12}>
        <ChartCard
          title="经费使用情况"
          chartType="column"
          data={[
            { type: '已下拨', value: userStats?.fund.total_allocated || 0 },
            { type: '已支出', value: userStats?.fund.total_expended || 0 },
          ]}
          config={{
            xField: 'type',
            yField: 'value',
          }}
        />
      </Col>
    </Row>
  ),
}
```

## Ant Design Charts配置

ChartCard组件已经配置了冰川蓝主题色系，您可以根据需要自定义配置：

### 柱状图配置
```javascript
config={{
  xField: 'category',    // X轴字段
  yField: 'value',       // Y轴字段
  columnWidthRatio: 0.6, // 柱宽比例
  label: {               // 标签
    position: 'middle',
    style: {
      fill: '#FFFFFF',
      opacity: 0.6,
    },
  },
}}
```

### 饼图配置
```javascript
config={{
  angleField: 'value',   // 角度字段
  colorField: 'type',    // 颜色字段
  radius: 0.8,          // 半径
  label: {
    type: 'outer',
    content: '{name} {percentage}',
  },
}}
```

### 折线图配置
```javascript
config={{
  xField: 'date',        // X轴字段
  yField: 'value',       // Y轴字段
  smooth: true,         // 平滑曲线
  point: {              // 点配置
    size: 4,
    shape: 'circle',
  },
}}
```

## 注意事项

1. **数据格式**: 所有统计数据API返回的数据格式已统一，可直接用于图表组件
2. **错误处理**: 建议在每个统计API调用时添加错误处理
3. **加载状态**: 建议添加loading状态，提升用户体验
4. **权限控制**: 各统计API已实现权限控制，只有相应角色可以访问

## 后续扩展建议

1. 添加更多图表类型（如雷达图、热力图等）
2. 添加图表导出功能（PNG/PDF）
3. 添加数据筛选功能（时间范围、状态筛选等）
4. 添加图表交互功能（下钻、联动等）
5. 添加实时数据更新（WebSocket）
