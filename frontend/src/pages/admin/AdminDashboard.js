import React, { useState, useEffect } from 'react';
import { Table, Card, Button, Tag, Modal, Form, Input, Select, message, theme, Tabs } from 'antd';
import { UserOutlined, PlusOutlined, TeamOutlined } from '@ant-design/icons';
import { commonApi, userApi, teamApi } from '../../api/api';

const AdminDashboard = () => {
  const { token } = theme.useToken();
  const [users, setUsers] = useState([]);
  const [teams, setTeams] = useState([]);
  const [createModal, setCreateModal] = useState(false);
  const [form] = Form.useForm();

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    const uRes = await commonApi.getAllUsers();
    setUsers(uRes.data);
    const tRes = await teamApi.getAll();
    setTeams(tRes.data);
  };

  const handleCreate = async (values) => {
    try {
      await userApi.adminCreateUser(values);
      message.success('用户创建成功');
      setCreateModal(false);
      form.resetFields();
      loadData();
    } catch(e) {}
  };

  const userColumns = [
    { title: '用户名', dataIndex: 'user_name' },
    { title: '姓名', dataIndex: 'real_name' },
    { title: '角色', dataIndex: 'role', render: r => <Tag color="geekblue">{r}</Tag> },
    { title: '单位', dataIndex: 'affiliation' }
  ];

  const teamColumns = [
    { title: '团队名称', dataIndex: 'team_name', render: t => <b>{t}</b> },
    { title: '队长', dataIndex: 'leader_name' },
    { title: '人数', dataIndex: 'member_count' }
  ];

  return (
    <Card title="系统管理台" style={{ borderRadius: token.borderRadius }}>
      <Button type="primary" icon={<PlusOutlined />} style={{ marginBottom: 16 }} onClick={() => setCreateModal(true)}>
        创建新账号
      </Button>
      <Tabs items={[
        { key: '1', label: <span><UserOutlined /> 账号管理</span>, children: <Table dataSource={users} columns={userColumns} rowKey="user_id" /> },
        { key: '2', label: <span><TeamOutlined /> 团队概览</span>, children: <Table dataSource={teams} columns={teamColumns} rowKey="team_id" /> }
      ]} />

      <Modal title="创建用户" open={createModal} footer={null} onCancel={() => setCreateModal(false)}>
        <Form form={form} onFinish={handleCreate} layout="vertical">
          <Form.Item name="user_name" label="用户名" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="real_name" label="真实姓名" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="password" label="初始密码" rules={[{ required: true }]}><Input.Password /></Form.Item>
          <Form.Item name="role" label="角色" rules={[{ required: true }]}>
            <Select>
              <Select.Option value="评审人">评审人</Select.Option>
              <Select.Option value="秘书">秘书</Select.Option>
              <Select.Option value="管理员">管理员</Select.Option>
              <Select.Option value="项目参与者">项目参与者</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item name="affiliation" label="单位"><Input /></Form.Item>
          <Button type="primary" htmlType="submit" block>创建</Button>
        </Form>
      </Modal>
    </Card>
  );
};

export default AdminDashboard;
