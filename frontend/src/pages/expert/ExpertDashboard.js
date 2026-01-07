import React, { useState, useEffect } from 'react';
import { Card, List, Button, Statistic, Row, Col, Drawer, Input, Slider, message, theme, Tag, Empty, Space } from 'antd';
import { FormOutlined, ClockCircleOutlined, ReloadOutlined } from '@ant-design/icons';
import { reviewApi } from '../../api/api';

const ExpertDashboard = () => {
  const { token } = theme.useToken();
  const [tasks, setTasks] = useState([]);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [currentTask, setCurrentTask] = useState(null);
  const [reviewData, setReviewData] = useState({ innovation: 20, feasibility: 20, teamwork: 30, comment: '' });

  useEffect(() => { loadTasks(); }, []);

  const loadTasks = async () => {
    try {
      const res = await reviewApi.getMyTasks();
      setTasks(res.data);
    } catch (e) {}
  };

  const openReview = (task) => {
    setCurrentTask(task);
    setDrawerOpen(true);
  };

  const handleSubmitReview = async () => {
    try {
      await reviewApi.submitReview(currentTask.task_id, reviewData);
      message.success('评审意见已提交');
      setDrawerOpen(false);
      loadTasks(); // 刷新列表
    } catch (e) {}
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      <Row gutter={24}>
        <Col span={8}><Card><Statistic title="待评审任务" value={tasks.filter(t => t.status !== '已完成').length} /></Card></Col>
        <Col span={8}><Card><Statistic title="已完成任务" value={tasks.filter(t => t.status === '已完成').length} valueStyle={{ color: token.colorSuccess }} /></Card></Col>
      </Row>

      <Card title="我的评审任务" extra={<Button icon={<ReloadOutlined />} onClick={loadTasks}>刷新</Button>} style={{ borderRadius: token.borderRadius }}>
        <List
          dataSource={tasks}
          locale={{ emptyText: <Empty description="暂无分配的任务" /> }}
          renderItem={(item) => (
            <List.Item actions={[
              item.status === '已完成' ? <Tag color="green">已提交</Tag> :
                <Button type="primary" onClick={() => openReview(item)}>开始评审</Button>
            ]}>
              <List.Item.Meta
                avatar={<FormOutlined style={{ fontSize: 24, color: token.colorPrimary }} />}
                title={item.project_name}
                description={
                  <Space>
                    <Tag>{item.domain}</Tag>
                    <Tag icon={<ClockCircleOutlined />}>截止: {item.deadline}</Tag>
                  </Space>
                }
              />
            </List.Item>
          )}
        />
      </Card>

      <Drawer title="项目评审" width={500} onClose={() => setDrawerOpen(false)} open={drawerOpen} footer={
        <Button type="primary" block onClick={handleSubmitReview}>提交评审结论</Button>
      }>
        <div style={{ marginBottom: 24 }}>
          <h4>创新性 (25分)</h4>
          <Slider max={25} value={reviewData.innovation} onChange={v => setReviewData({...reviewData, innovation: v})} />
        </div>
        <div style={{ marginBottom: 24 }}>
          <h4>可行性 (25分)</h4>
          <Slider max={25} value={reviewData.feasibility} onChange={v => setReviewData({...reviewData, feasibility: v})} />
        </div>
        <div style={{ marginBottom: 24 }}>
          <h4>市场潜力 (15分)</h4>
          <Slider max={15} value={reviewData.marketPotential} onChange={v => setReviewData({...reviewData, marketPotential: v})} />
        </div>
        <div style={{ marginBottom: 24 }}>
          <h4>团队能力 (35分)</h4>
          <Slider max={35} value={reviewData.teamwork} onChange={v => setReviewData({...reviewData, teamwork: v})} />
        </div>
        <Input.TextArea rows={6} placeholder="评审意见..." value={reviewData.comment} onChange={e => setReviewData({...reviewData, comment: e.target.value})} />
      </Drawer>
    </div>
  );
};

export default ExpertDashboard;
