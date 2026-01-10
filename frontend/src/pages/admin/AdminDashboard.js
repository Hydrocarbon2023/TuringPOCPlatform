import React, {useState, useEffect} from 'react';
import {Table, Tag, Modal, Form, Input, Select, message, Tabs, Typography, Row, Col, Space} from 'antd';
import {
  UserOutlined,
  PlusOutlined,
  TeamOutlined,
  UsergroupAddOutlined,
  TeamOutlined as TeamIcon
} from '@ant-design/icons';
import {commonApi, userApi, teamApi} from '../../api/api';
import GlassCard from '../../components/GlassCard';
import AnimatedButton from '../../components/AnimatedButton';
import StatCard from '../../components/StatCard';
import {glacierTheme} from '../../styles/theme';

const {Title} = Typography;

const AdminDashboard = () => {
  const [users, setUsers] = useState([]);
  const [teams, setTeams] = useState([]);
  const [createModal, setCreateModal] = useState(false);
  const [form] = Form.useForm();

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const uRes = await commonApi.getAllUsers();
      setUsers(uRes.data);
      const tRes = await teamApi.getAll();
      setTeams(tRes.data);
    } catch (e) {
    }
  };

  const handleCreate = async (values) => {
    try {
      await userApi.adminCreateUser(values);
      message.success('用户创建成功');
      setCreateModal(false);
      form.resetFields();
      loadData();
    } catch (e) {
    }
  };

  const userColumns = [
    {
      title: '用户名',
      dataIndex: 'user_name',
      render: t => <span style={{fontWeight: 500, color: glacierTheme.colors.text}}>{t}</span>
    },
    {
      title: '姓名',
      dataIndex: 'real_name',
      render: n => <span style={{color: glacierTheme.colors.textSecondary}}>{n || '-'}</span>
    },
    {
      title: '角色',
      dataIndex: 'role',
      render: r => (
        <Tag style={{
          background: `${glacierTheme.colors.info}20`,
          border: `1px solid ${glacierTheme.colors.info}`,
          color: glacierTheme.colors.info,
        }}>
          {r}
        </Tag>
      )
    },
    {
      title: '单位',
      dataIndex: 'affiliation',
      render: a => <span style={{color: glacierTheme.colors.textSecondary}}>{a || '-'}</span>
    }
  ];

  const teamColumns = [
    {
      title: '团队名称',
      dataIndex: 'team_name',
      render: t => <span style={{fontWeight: 600, color: glacierTheme.colors.text}}>{t}</span>
    },
    {
      title: '队长',
      dataIndex: 'leader_name',
      render: n => <span style={{color: glacierTheme.colors.textSecondary}}>{n || '未知'}</span>
    },
    {
      title: '人数',
      dataIndex: 'member_count',
      render: c => <span style={{color: glacierTheme.colors.textSecondary}}>{c || 0}</span>
    }
  ];

  const userCount = users.length;
  const teamCount = teams.length;
  const reviewerCount = users.filter(u => u.role === '评审人').length;

  return (
    <div style={{display: 'flex', flexDirection: 'column', gap: glacierTheme.spacing.xl}}>
      {/* 统计卡片 */}
      <Row gutter={[glacierTheme.spacing.lg, glacierTheme.spacing.lg]}>
        <Col xs={24} sm={12} lg={8}>
          <StatCard
            title="总用户数"
            value={userCount}
            icon={<UserOutlined/>}
            color="primary"
          />
        </Col>
        <Col xs={24} sm={12} lg={8}>
          <StatCard
            title="总团队数"
            value={teamCount}
            icon={<TeamOutlined/>}
            color="info"
          />
        </Col>
        <Col xs={24} sm={12} lg={8}>
          <StatCard
            title="评审人数"
            value={reviewerCount}
            icon={<UsergroupAddOutlined/>}
            color="success"
          />
        </Col>
      </Row>

      {/* 主内容区 */}
      <GlassCard>
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: glacierTheme.spacing.lg,
          flexWrap: 'wrap',
          gap: glacierTheme.spacing.md,
        }}>
          <Title level={4} style={{margin: 0, color: glacierTheme.colors.text, fontWeight: 600}}>
            系统管理台
          </Title>
          <AnimatedButton
            type="primary"
            icon={<PlusOutlined/>}
            onClick={() => setCreateModal(true)}
          >
            创建新账号
          </AnimatedButton>
        </div>
        <Tabs
          items={[
            {
              key: '1',
              label: (
                <span style={{fontSize: '15px', fontWeight: 500}}>
                  <UserOutlined style={{marginRight: glacierTheme.spacing.xs}}/>
                  账号管理
                </span>
              ),
              children: (
                <Table
                  dataSource={users}
                  columns={userColumns}
                  rowKey="user_id"
                  pagination={{
                    pageSize: 10,
                    showSizeChanger: true,
                    showTotal: (total) => `共 ${total} 条`,
                  }}
                />
              )
            },
            {
              key: '2',
              label: (
                <span style={{fontSize: '15px', fontWeight: 500}}>
                  <TeamIcon style={{marginRight: glacierTheme.spacing.xs}}/>
                  团队概览
                </span>
              ),
              children: (
                <Table
                  dataSource={teams}
                  columns={teamColumns}
                  rowKey="team_id"
                  pagination={{
                    pageSize: 10,
                    showSizeChanger: true,
                    showTotal: (total) => `共 ${total} 条`,
                  }}
                />
              )
            }
          ]}
        />
      </GlassCard>

      {/* 创建用户模态框 */}
      <Modal
        title={
          <span style={{fontSize: '18px', fontWeight: 600, color: glacierTheme.colors.text}}>
            创建用户
          </span>
        }
        open={createModal}
        footer={null}
        onCancel={() => setCreateModal(false)}
        styles={{
          content: {
            background: glacierTheme.colors.background,
          },
        }}
      >
        <Form form={form} onFinish={handleCreate} layout="vertical">
          <Form.Item name="user_name" label="用户名" rules={[{required: true, message: '请输入用户名'}]}>
            <Input style={{borderRadius: glacierTheme.borderRadius.md}}/>
          </Form.Item>
          <Form.Item name="real_name" label="真实姓名" rules={[{required: true, message: '请输入真实姓名'}]}>
            <Input style={{borderRadius: glacierTheme.borderRadius.md}}/>
          </Form.Item>
          <Form.Item name="password" label="初始密码" rules={[{required: true, message: '请输入初始密码'}]}>
            <Input.Password style={{borderRadius: glacierTheme.borderRadius.md}}/>
          </Form.Item>
          <Form.Item name="role" label="角色" rules={[{required: true, message: '请选择角色'}]}>
            <Select style={{borderRadius: glacierTheme.borderRadius.md}}>
              <Select.Option value="评审人">评审人</Select.Option>
              <Select.Option value="秘书">秘书</Select.Option>
              <Select.Option value="管理员">管理员</Select.Option>
              <Select.Option value="项目参与者">项目参与者</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item name="affiliation" label="单位">
            <Input style={{borderRadius: glacierTheme.borderRadius.md}}/>
          </Form.Item>
          <AnimatedButton type="primary" htmlType="submit" block>
            创建
          </AnimatedButton>
        </Form>
      </Modal>
    </div>
  );
};

export default AdminDashboard;
