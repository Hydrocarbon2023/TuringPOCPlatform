import React, {useState, useEffect} from 'react';
import {
  Table,
  Button,
  Tag,
  Modal,
  Radio,
  Input,
  message,
  Select,
  DatePicker,
  Form,
  Space,
  Typography,
  Row,
  Col
} from 'antd';
import {AuditOutlined, SendOutlined, ReloadOutlined, FileTextOutlined, CheckCircleOutlined} from '@ant-design/icons';
import {projectApi, commonApi} from '../../api/api';
import GlassCard from '../../components/GlassCard';
import AnimatedButton from '../../components/AnimatedButton';
import StatCard from '../../components/StatCard';
import {glacierTheme} from '../../styles/theme';

const {Title} = Typography;

const SecretaryDashboard = () => {
  const [projects, setProjects] = useState([]);
  const [users, setUsers] = useState([]);
  const [auditModal, setAuditModal] = useState({open: false, projectId: null});
  const [assignModal, setAssignModal] = useState({open: false, projectId: null});
  const [auditResult, setAuditResult] = useState('通过');
  const [comment, setComment] = useState('');
  const [assignForm] = Form.useForm();

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const pRes = await projectApi.getAll();
      setProjects(pRes.data);
      const uRes = await commonApi.getAllUsers();
      setUsers(uRes.data);
    } catch (e) {
    }
  };

  const handleAudit = async () => {
    try {
      await projectApi.audit(auditModal.projectId, {result: auditResult, comment});
      message.success('初审完成');
      setAuditModal({open: false, projectId: null});
      setComment('');
      loadData();
    } catch (e) {
    }
  };

  const handleAssign = async (values) => {
    try {
      await projectApi.assignReviewer(assignModal.projectId, {
        reviewer_id: values.reviewer_id,
        deadline: values.deadline?.format('YYYY-MM-DD')
      });
      message.success('已分配评审人');
      setAssignModal({open: false, projectId: null});
      assignForm.resetFields();
      loadData();
    } catch (e) {
    }
  };

  const columns = [
    {
      title: '项目名称',
      dataIndex: 'project_name',
      render: t => <span style={{fontWeight: 600, color: glacierTheme.colors.text}}>{t}</span>
    },
    {
      title: '申请人',
      dataIndex: 'principal_name',
      render: n => <span style={{color: glacierTheme.colors.textSecondary}}>{n}</span>
    },
    {
      title: '状态',
      dataIndex: 'status',
      render: s => {
        const statusConfig = {
          '待初审': {color: glacierTheme.colors.warning, bg: `${glacierTheme.colors.warning}20`},
          '复审中': {color: glacierTheme.colors.info, bg: `${glacierTheme.colors.info}20`},
          '已通过': {color: glacierTheme.colors.success, bg: `${glacierTheme.colors.success}20`},
        };
        const config = statusConfig[s] || {color: glacierTheme.colors.textSecondary, bg: glacierTheme.colors.surface};
        return (
          <Tag style={{
            background: config.bg,
            border: `1px solid ${config.color}`,
            color: config.color,
          }}>
            {s}
          </Tag>
        );
      }
    },
    {
      title: '操作',
      render: (_, record) => (
        <Space>
          {record.status === '待初审' && (
            <AnimatedButton
              type="primary"
              size="small"
              icon={<AuditOutlined/>}
              onClick={() => setAuditModal({open: true, projectId: record.project_id})}
            >
              初审
            </AnimatedButton>
          )}
          {record.status === '复审中' && (
            <AnimatedButton
              size="small"
              icon={<SendOutlined/>}
              onClick={() => setAssignModal({open: true, projectId: record.project_id})}
              style={{
                border: `1px solid ${glacierTheme.colors.border}`,
                background: glacierTheme.colors.surface,
              }}
            >
              分配
            </AnimatedButton>
          )}
        </Space>
      ),
    },
  ];

  const pendingCount = projects.filter(p => p.status === '待初审').length;
  const reviewingCount = projects.filter(p => p.status === '复审中').length;
  const passedCount = projects.filter(p => p.status === '已通过').length;

  return (
    <div style={{display: 'flex', flexDirection: 'column', gap: glacierTheme.spacing.xl}}>
      {/* 统计卡片 */}
      <Row gutter={[glacierTheme.spacing.lg, glacierTheme.spacing.lg]}>
        <Col xs={24} sm={12} lg={8}>
          <StatCard
            title="待初审项目"
            value={pendingCount}
            icon={<FileTextOutlined/>}
            color="warning"
          />
        </Col>
        <Col xs={24} sm={12} lg={8}>
          <StatCard
            title="复审中项目"
            value={reviewingCount}
            icon={<AuditOutlined/>}
            color="info"
          />
        </Col>
        <Col xs={24} sm={12} lg={8}>
          <StatCard
            title="已通过项目"
            value={passedCount}
            icon={<CheckCircleOutlined/>}
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
            秘书控制台
          </Title>
          <AnimatedButton
            icon={<ReloadOutlined/>}
            onClick={loadData}
            style={{
              border: `1px solid ${glacierTheme.colors.border}`,
              background: glacierTheme.colors.surface,
            }}
          >
            刷新列表
          </AnimatedButton>
        </div>
        <Table
          dataSource={projects}
          columns={columns}
          rowKey="project_id"
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showTotal: (total) => `共 ${total} 条`,
          }}
        />
      </GlassCard>

      {/* 项目初审模态框 */}
      <Modal
        title={
          <span style={{fontSize: '18px', fontWeight: 600, color: glacierTheme.colors.text}}>
            项目初审
          </span>
        }
        open={auditModal.open}
        onOk={handleAudit}
        onCancel={() => {
          setAuditModal({open: false});
          setComment('');
        }}
        okText="确认"
        cancelText="取消"
        styles={{
          content: {
            background: glacierTheme.colors.background,
          },
        }}
      >
        <Radio.Group
          value={auditResult}
          onChange={e => setAuditResult(e.target.value)}
          style={{
            marginBottom: glacierTheme.spacing.lg,
            width: '100%',
          }}
        >
          <Radio.Button
            value="通过"
            style={{
              flex: 1,
              textAlign: 'center',
              borderRadius: glacierTheme.borderRadius.md,
            }}
          >
            通过
          </Radio.Button>
          <Radio.Button
            value="未通过"
            style={{
              flex: 1,
              textAlign: 'center',
              borderRadius: glacierTheme.borderRadius.md,
            }}
          >
            驳回
          </Radio.Button>
        </Radio.Group>
        <Input.TextArea
          rows={4}
          placeholder="请输入初审意见..."
          value={comment}
          onChange={e => setComment(e.target.value)}
          style={{
            borderRadius: glacierTheme.borderRadius.md,
            border: `1px solid ${glacierTheme.colors.border}`,
          }}
        />
      </Modal>

      {/* 分配评审人模态框 */}
      <Modal
        title={
          <span style={{fontSize: '18px', fontWeight: 600, color: glacierTheme.colors.text}}>
            分配评审人
          </span>
        }
        open={assignModal.open}
        footer={null}
        onCancel={() => setAssignModal({open: false})}
        styles={{
          content: {
            background: glacierTheme.colors.background,
          },
        }}
      >
        <Form form={assignForm} onFinish={handleAssign} layout="vertical">
          <Form.Item name="reviewer_id" label="评审人" rules={[{required: true, message: '请选择评审人'}]}>
            <Select
              showSearch
              optionFilterProp="label"
              placeholder="请选择评审人"
              style={{
                borderRadius: glacierTheme.borderRadius.md,
              }}
            >
              {users.filter(u => u.role === '评审人').map(u => (
                <Select.Option key={u.user_id} value={u.user_id} label={u.real_name}>
                  {u.real_name}
                </Select.Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item name="deadline" label="截止日期">
            <DatePicker
              style={{width: '100%', borderRadius: glacierTheme.borderRadius.md}}
            />
          </Form.Item>
          <AnimatedButton type="primary" htmlType="submit" block>
            分配
          </AnimatedButton>
        </Form>
      </Modal>
    </div>
  );
};

export default SecretaryDashboard;
