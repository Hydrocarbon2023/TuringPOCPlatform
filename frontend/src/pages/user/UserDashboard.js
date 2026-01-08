import React, { useState, useEffect } from 'react';
import { Tabs, Card, Table, Tag, Button, Modal, Form, Input, message, Descriptions, theme, Space, List } from 'antd';
import { ProjectOutlined, TeamOutlined, PlusOutlined, UserAddOutlined } from '@ant-design/icons';
import { projectApi, teamApi } from '../../api/api';

const UserDashboard = () => {
  const { token } = theme.useToken();
  const [projects, setProjects] = useState([]);
  const [myTeams, setMyTeams] = useState([]);

  const [teamModal, setTeamModal] = useState(false);
  const [inviteModal, setInviteModal] = useState({ open: false, teamId: null });
  const [detailModal, setDetailModal] = useState({ open: false, data: null });
  const [declareModal, setDeclareModal] = useState(false);
  const [form] = Form.useForm();

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    try {
      const pRes = await projectApi.getAll();
      setProjects(pRes.data);
      const tRes = await teamApi.getMyTeams();
      setMyTeams(tRes.data);
    } catch(e) {}
  };

  const handleCreateTeam = async (values) => {
    try {
      await teamApi.create(values);
      message.success('团队创建成功');
      setTeamModal(false);
      loadData();
    } catch(e) {}
  };

  const handleInvite = async (values) => {
    try {
      await teamApi.inviteMember(inviteModal.teamId, values);
      message.success('邀请发送成功');
      setInviteModal({ open: false, teamId: null });
    } catch(e) {}
  };

  const handleDeclare = async (values) => {
    try {
      await projectApi.create(values);
      message.success('申报成功');
      setDeclareModal(false);
      form.resetFields();
      loadData();
    } catch(e) {}
  };

  const showDetail = async (id) => {
    const res = await projectApi.getDetail(id);
    setDetailModal({ open: true, data: res.data });
  };

  const projectColumns = [
    { title: '项目名称', dataIndex: 'project_name', render: t => <b style={{ color: token.colorTextHeading }}>{t}</b> },
    { title: '负责人', dataIndex: 'principal_name', render: n => <span style={{ color: token.colorTextSecondary }}>{n}</span> },
    { title: '领域', dataIndex: 'domain', render: t => <Tag>{t}</Tag> },
    { title: '状态', dataIndex: 'status', render: s => <Tag color={s === '已通过' ? 'green' : 'blue'}>{s}</Tag> },
    { title: '操作', render: (_, r) => <Button type="link" onClick={() => showDetail(r.project_id)}>详情</Button> }
  ];

  const teamColumns = [
    { title: '团队名称', dataIndex: 'team_name', render: t => <b>{t}</b> },
    { title: '队长', dataIndex: 'leader_name' },
    { title: '我的角色', dataIndex: 'role', render: r => <Tag color={r==='队长'?'gold':'default'}>{r}</Tag> },
    { title: '操作', render: (_, r) => r.role === '队长' && <Button size="small" icon={<UserAddOutlined />} onClick={() => setInviteModal({ open: true, teamId: r.team_id })}>邀请</Button> }
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      <div style={{ background: token.colorBgContainer, padding: 24, borderRadius: token.borderRadius, display: 'flex', justifyContent: 'space-between' }}>
        <div><h2 style={{ margin: 0 }}>项目工作台</h2></div>
        <Space>
          <Button icon={<TeamOutlined />} onClick={() => setTeamModal(true)}>创建团队</Button>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setDeclareModal(true)}>申报项目</Button>
        </Space>
      </div>

      <Card style={{ borderRadius: token.borderRadius }}>
        <Tabs items={[
          { key: '1', label: <span><ProjectOutlined /> 项目列表</span>, children: <Table dataSource={projects} columns={projectColumns} rowKey="project_id" /> },
          { key: '2', label: <span><TeamOutlined /> 我的团队</span>, children: <Table dataSource={myTeams} columns={teamColumns} rowKey="team_id" /> }
        ]} />
      </Card>

      <Modal title="申报新项目" open={declareModal} footer={null} onCancel={() => setDeclareModal(false)}>
        <Form form={form} onFinish={handleDeclare} layout="vertical">
          <Form.Item name="project_name" label="名称" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="domain" label="领域" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="project_description" label="简介"><Input.TextArea /></Form.Item>
          <Button type="primary" htmlType="submit" block>提交申报</Button>
        </Form>
      </Modal>

      <Modal title="组建团队" open={teamModal} footer={null} onCancel={() => setTeamModal(false)}>
        <Form onFinish={handleCreateTeam} layout="vertical">
          <Form.Item name="team_name" label="名称" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="domain" label="领域"><Input /></Form.Item>
          <Button type="primary" htmlType="submit" block>创建</Button>
        </Form>
      </Modal>

      <Modal title="邀请成员" open={inviteModal.open} footer={null} onCancel={() => setInviteModal({ open: false, teamId: null })}>
        <Form onFinish={handleInvite} layout="vertical">
          <Form.Item name="user_name" label="用户名" rules={[{ required: true }]}><Input /></Form.Item>
          <Button type="primary" htmlType="submit" block>邀请</Button>
        </Form>
      </Modal>

      <Modal title="项目详情" open={detailModal.open} onCancel={() => setDetailModal({ open: false, data: null })} footer={null} width={700}>
        {detailModal.data && (
          <Descriptions bordered column={1}>
            <Descriptions.Item label="名称">{detailModal.data.project_name}</Descriptions.Item>
            <Descriptions.Item label="负责人">{detailModal.data.principal_name}</Descriptions.Item>
            <Descriptions.Item label="状态"><Tag color="geekblue">{detailModal.data.status}</Tag></Descriptions.Item>

            {/* 【修改点】只要 review_info 存在且有分，就显示结果区 */}
            {detailModal.data.review_info && detailModal.data.review_info.avg_score > 0 && (
              <Descriptions.Item label="复审结果">
                <div style={{ padding: 12, background: '#f6ffed', border: '1px solid #b7eb8f', borderRadius: 6 }}>
                  <div style={{ marginBottom: 4 }}>专家评审均分：<b style={{ fontSize: 20, color: '#135200' }}>{detailModal.data.review_info.avg_score}</b> 分</div>
                  <div style={{ color: '#888', fontSize: 12 }}>（基于 {detailModal.data.review_info.review_count} 位专家的评分）</div>
                  <div style={{ marginTop: 8, fontWeight: 'bold' }}>
                    {detailModal.data.review_info.avg_score > 60 ?
                      <span style={{ color: 'green' }}>✅ 分数达标，项目已通过复审。</span> :
                      <span style={{ color: 'red' }}>❌ 分数未达标 (需>60)，项目未通过。</span>
                    }
                  </div>
                </div>
              </Descriptions.Item>
            )}

            <Descriptions.Item label="简介">{detailModal.data.project_description}</Descriptions.Item>
          </Descriptions>
        )}
      </Modal>
    </div>
  );
};

export default UserDashboard;
