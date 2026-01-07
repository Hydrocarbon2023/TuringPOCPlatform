import React, { useState, useEffect } from 'react';
import { Table, Card, Button, Tabs, Tag, Modal, Radio, Input, message, Space, theme, Avatar, Select, DatePicker, Form } from 'antd';
import { CheckCircleOutlined, UserOutlined, AuditOutlined, PlusOutlined, SendOutlined } from '@ant-design/icons';
import { projectApi, commonApi, userApi } from '../../api/api';

const AdminDashboard = () => {
  const { token } = theme.useToken();
  const [projects, setProjects] = useState([]);
  const [users, setUsers] = useState([]);

  // 模态框状态
  const [auditModal, setAuditModal] = useState({ open: false, projectId: null });
  const [assignModal, setAssignModal] = useState({ open: false, projectId: null });
  const [createUserModal, setCreateUserModal] = useState(false);

  // 表单数据
  const [auditResult, setAuditResult] = useState('通过');
  const [comment, setComment] = useState('');
  const [assignForm] = Form.useForm();
  const [userForm] = Form.useForm();

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    try {
      const pRes = await projectApi.getAll();
      const uRes = await commonApi.getAllUsers();
      setProjects(pRes.data);
      setUsers(uRes.data);
    } catch(e) {}
  };

  // 提交审核
  const handleAuditSubmit = async () => {
    try {
      await projectApi.audit(auditModal.projectId, { result: auditResult, comment });
      message.success('审核已完成');
      setAuditModal({ open: false, projectId: null });
      loadData();
    } catch (e) {}
  };

  // 提交分配
  const handleAssignSubmit = async (values) => {
    try {
      await projectApi.assignExpert(assignModal.projectId, {
        expert_id: values.expert_id,
        deadline: values.deadline ? values.deadline.format('YYYY-MM-DD') : null
      });
      message.success('已分配给专家');
      setAssignModal({ open: false, projectId: null });
      assignForm.resetFields();
    } catch (e) {}
  };

  // 创建用户
  const handleCreateUser = async (values) => {
    try {
      await userApi.adminCreateUser(values);
      message.success('用户创建成功');
      setCreateUserModal(false);
      userForm.resetFields();
      loadData();
    } catch (e) {}
  };

  const projectColumns = [
    { title: '项目名称', dataIndex: 'project_name', render: t => <b>{t}</b> },
    { title: '申请人', dataIndex: 'principal_name' },
    { title: '状态', dataIndex: 'status', render: s => <Tag color={s === '复审中' ? 'blue' : (s === '待初审' ? 'orange' : 'default')}>{s}</Tag> },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Space>
          {/* 待初审 -> 显示审核按钮 */}
          {record.status === '待初审' && (
            <Button type="primary" size="small" onClick={() => setAuditModal({ open: true, projectId: record.project_id })}>
              初审
            </Button>
          )}
          {/* 复审中 -> 显示分配专家按钮 */}
          {record.status === '复审中' && (
            <Button size="small" icon={<SendOutlined />} onClick={() => setAssignModal({ open: true, projectId: record.project_id })}>
              分配专家
            </Button>
          )}
        </Space>
      ),
    },
  ];

  const userColumns = [
    { title: '用户名', dataIndex: 'user_name' },
    { title: '姓名', dataIndex: 'real_name' },
    { title: '角色', dataIndex: 'role', render: r => <Tag color="geekblue">{r}</Tag> },
  ];

  return (
    <Card bordered={false} style={{ borderRadius: token.borderRadius }}>
      <div style={{ marginBottom: 24, display: 'flex', justifyContent: 'space-between' }}>
        <h2 style={{ margin: 0 }}>管理控制台</h2>
        <Button onClick={loadData}>刷新数据</Button>
      </div>

      <Tabs defaultActiveKey="1" items={[
        {
          key: '1', label: <span><AuditOutlined /> 项目管理</span>,
          children: <Table dataSource={projects} columns={projectColumns} rowKey="project_id" />
        },
        {
          key: '2', label: <span><UserOutlined /> 用户管理</span>,
          children: (
            <div>
              <Button type="primary" icon={<PlusOutlined />} style={{ marginBottom: 16 }} onClick={() => setCreateUserModal(true)}>
                新建用户
              </Button>
              <Table dataSource={users} columns={userColumns} rowKey="user_id" />
            </div>
          )
        }
      ]} />

      {/* 1. 审核弹窗 */}
      <Modal title="项目初审" open={auditModal.open} onOk={handleAuditSubmit} onCancel={() => setAuditModal({ open: false, projectId: null })}>
        <Radio.Group value={auditResult} onChange={e => setAuditResult(e.target.value)} style={{ marginBottom: 16 }}>
          <Radio.Button value="通过">通过 (进入复审)</Radio.Button>
          <Radio.Button value="未通过">驳回</Radio.Button>
        </Radio.Group>
        <Input.TextArea rows={3} placeholder="审核意见" value={comment} onChange={e => setComment(e.target.value)} />
      </Modal>

      {/* 2. 分配专家弹窗 */}
      <Modal title="分配评审专家" open={assignModal.open} onCancel={() => setAssignModal({ open: false, projectId: null })} footer={null}>
        <Form form={assignForm} onFinish={handleAssignSubmit} layout="vertical">
          <Form.Item name="expert_id" label="选择专家" rules={[{ required: true }]}>
            <Select placeholder="请选择专家">
              {users.filter(u => u.role === '评审人').map(u => (
                <Select.Option key={u.user_id} value={u.user_id}>{u.real_name} ({u.affiliation})</Select.Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item name="deadline" label="截止日期">
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>
          <Button type="primary" htmlType="submit" block>确认分配</Button>
        </Form>
      </Modal>

      {/* 3. 新建用户弹窗 */}
      <Modal title="创建新用户" open={createUserModal} onCancel={() => setCreateUserModal(false)} footer={null}>
        <Form form={userForm} onFinish={handleCreateUser} layout="vertical">
          <Form.Item name="user_name" label="用户名" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="real_name" label="真实姓名" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="password" label="密码" rules={[{ required: true }]}><Input.Password /></Form.Item>
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
