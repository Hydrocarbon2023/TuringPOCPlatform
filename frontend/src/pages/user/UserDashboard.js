import React, {useState, useEffect} from 'react';
import {Tabs, Table, Tag, Modal, Form, Input, message, Descriptions, Space, Row, Col, Typography, Button} from 'antd';
import {ProjectOutlined, TeamOutlined, PlusOutlined, UserAddOutlined, FileTextOutlined, RocketOutlined} from '@ant-design/icons';
import {useNavigate} from 'react-router-dom';
import {projectApi, teamApi} from '../../api/api';
import GlassCard from '../../components/GlassCard';
import AnimatedButton from '../../components/AnimatedButton';
import StatCard from '../../components/StatCard';
import {glacierTheme} from '../../styles/theme';

const {Title} = Typography;

const UserDashboard = () => {
  const navigate = useNavigate();
  const [projects, setProjects] = useState([]);
  const [myTeams, setMyTeams] = useState([]);
  const [teamModal, setTeamModal] = useState(false);
  const [inviteModal, setInviteModal] = useState({open: false, teamId: null});
  const [detailModal, setDetailModal] = useState({open: false, data: null});
  const [declareModal, setDeclareModal] = useState(false);
  const [form] = Form.useForm();

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const pRes = await projectApi.getAll();
      setProjects(pRes.data);
      const tRes = await teamApi.getMyTeams();
      setMyTeams(tRes.data);
    } catch (e) {
    }
  };

  const handleCreateTeam = async (values) => {
    try {
      await teamApi.create(values);
      message.success('团队创建成功');
      setTeamModal(false);
      loadData();
    } catch (e) {
    }
  };

  const handleInvite = async (values) => {
    try {
      await teamApi.inviteMember(inviteModal.teamId, values);
      message.success('邀请发送成功');
      setInviteModal({open: false, teamId: null});
      loadData();
    } catch (e) {
    }
  };

  const handleDeclare = async (values) => {
    try {
      await projectApi.create(values);
      message.success('申报成功');
      setDeclareModal(false);
      form.resetFields();
      loadData();
    } catch (e) {
    }
  };

  const showDetail = async (id) => {
    const res = await projectApi.getDetail(id);
    setDetailModal({open: true, data: res.data});
  };

  const projectColumns = [
    {
      title: '项目名称',
      dataIndex: 'project_name',
      render: t => <span style={{fontWeight: 600, color: glacierTheme.colors.text}}>{t}</span>
    },
    {
      title: '负责人',
      dataIndex: 'principal_name',
      render: n => <span style={{color: glacierTheme.colors.textSecondary}}>{n}</span>
    },
    {
      title: '领域',
      dataIndex: 'domain',
      render: t => (
        <Tag style={{
          background: glacierTheme.colors.surface,
          border: `1px solid ${glacierTheme.colors.border}`,
          color: glacierTheme.colors.text,
        }}>
          {t}
        </Tag>
      )
    },
    {
      title: '状态',
      dataIndex: 'status',
      render: s => (
        <Tag style={{
          background: s === '已通过' ? `${glacierTheme.colors.success}20` : `${glacierTheme.colors.info}20`,
          border: `1px solid ${s === '已通过' ? glacierTheme.colors.success : glacierTheme.colors.info}`,
          color: s === '已通过' ? glacierTheme.colors.success : glacierTheme.colors.info,
        }}>
          {s}
        </Tag>
      )
    },
    {
      title: '操作',
      render: (_, r) => (
        <Space>
          <AnimatedButton
            type="default"
            onClick={() => showDetail(r.project_id)}
            style={{
              border: 'none',
              background: 'transparent',
              color: glacierTheme.colors.primary,
              padding: 0,
            }}
          >
            详情
          </AnimatedButton>
          {(r.status === '已通过' || r.status === '孵化中' || r.status === '概念验证中') && (
            <AnimatedButton
              type="default"
              icon={<RocketOutlined/>}
              onClick={() => navigate(`/incubation/${r.project_id}`)}
              style={{
                border: `1px solid ${glacierTheme.colors.primary}`,
                background: `${glacierTheme.colors.primary}10`,
                color: glacierTheme.colors.primary,
              }}
            >
              孵化管理
            </AnimatedButton>
          )}
        </Space>
      )
    }
  ];

  const teamColumns = [
    {title: '团队名称', dataIndex: 'team_name', render: t => <span style={{fontWeight: 600}}>{t}</span>},
    {title: '队长', dataIndex: 'leader_name'},
    {
      title: '我的角色',
      dataIndex: 'role',
      render: r => (
        <Tag style={{
          background: r === '队长' ? `${glacierTheme.colors.warning}20` : glacierTheme.colors.surface,
          border: `1px solid ${r === '队长' ? glacierTheme.colors.warning : glacierTheme.colors.border}`,
          color: r === '队长' ? glacierTheme.colors.warning : glacierTheme.colors.text,
        }}>
          {r}
        </Tag>
      )
    },
    {
      title: '操作',
      render: (_, r) => r.role === '队长' && (
        <AnimatedButton
          type="default"
          icon={<UserAddOutlined/>}
          onClick={() => setInviteModal({open: true, teamId: r.team_id})}
          style={{
            border: 'none',
            background: 'transparent',
            color: glacierTheme.colors.primary,
          }}
        >
          邀请
        </AnimatedButton>
      )
    }
  ];

  return (
    <div style={{display: 'flex', flexDirection: 'column', gap: glacierTheme.spacing.xl}}>
      {/* 统计卡片 */}
      <Row gutter={[glacierTheme.spacing.lg, glacierTheme.spacing.lg]}>
        <Col xs={24} sm={12} lg={8}>
          <StatCard
            title="我的项目"
            value={projects.length}
            icon={<ProjectOutlined/>}
            color="primary"
          />
        </Col>
        <Col xs={24} sm={12} lg={8}>
          <StatCard
            title="我的团队"
            value={myTeams.length}
            icon={<TeamOutlined/>}
            color="info"
          />
        </Col>
        <Col xs={24} sm={12} lg={8}>
          <StatCard
            title="已通过项目"
            value={projects.filter(p => p.status === '已通过').length}
            icon={<FileTextOutlined/>}
            color="success"
          />
        </Col>
      </Row>

      {/* 操作栏 */}
      <GlassCard>
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: glacierTheme.spacing.md,
        }}>
          <Title level={4} style={{margin: 0, color: glacierTheme.colors.text, fontWeight: 600}}>
            项目工作台
          </Title>
          <Space>
            <AnimatedButton
              icon={<TeamOutlined/>}
              onClick={() => setTeamModal(true)}
              style={{
                border: `1px solid ${glacierTheme.colors.border}`,
                background: glacierTheme.colors.surface,
              }}
            >
              创建团队
            </AnimatedButton>
            <AnimatedButton
              type="primary"
              icon={<PlusOutlined/>}
              onClick={() => setDeclareModal(true)}
            >
              申报项目
            </AnimatedButton>
          </Space>
        </div>
      </GlassCard>

      {/* 内容区域 */}
      <GlassCard>
        <Tabs
          items={[
            {
              key: '1',
              label: (
                <span style={{fontSize: '15px', fontWeight: 500}}>
                  <ProjectOutlined style={{marginRight: glacierTheme.spacing.xs}}/>
                  项目列表
                </span>
              ),
              children: (
                <Table
                  dataSource={projects}
                  columns={projectColumns}
                  rowKey="project_id"
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
                  <TeamOutlined style={{marginRight: glacierTheme.spacing.xs}}/>
                  我的团队
                </span>
              ),
              children: (
                <Table
                  dataSource={myTeams}
                  columns={teamColumns}
                  rowKey="team_id"
                  pagination={false}
                />
              )
            }
          ]}
        />
      </GlassCard>

      {/* 申报项目模态框 */}
      <Modal
        title={
          <span style={{fontSize: '18px', fontWeight: 600, color: glacierTheme.colors.text}}>
            申报新项目
          </span>
        }
        open={declareModal}
        footer={null}
        onCancel={() => setDeclareModal(false)}
        styles={{
          content: {
            background: glacierTheme.colors.background,
          },
        }}
      >
        <Form form={form} onFinish={handleDeclare} layout="vertical">
          <Form.Item name="project_name" label="名称" rules={[{required: true}]}>
            <Input style={{borderRadius: glacierTheme.borderRadius.md}}/>
          </Form.Item>
          <Form.Item name="domain" label="领域" rules={[{required: true}]}>
            <Input style={{borderRadius: glacierTheme.borderRadius.md}}/>
          </Form.Item>
          <Form.Item name="project_description" label="简介">
            <Input.TextArea rows={4} style={{borderRadius: glacierTheme.borderRadius.md}}/>
          </Form.Item>
          <AnimatedButton type="primary" htmlType="submit" block>
            提交申报
          </AnimatedButton>
        </Form>
      </Modal>

      {/* 组建团队模态框 */}
      <Modal
        title={
          <span style={{fontSize: '18px', fontWeight: 600, color: glacierTheme.colors.text}}>
            组建团队
          </span>
        }
        open={teamModal}
        footer={null}
        onCancel={() => setTeamModal(false)}
        styles={{
          content: {
            background: glacierTheme.colors.background,
          },
        }}
      >
        <Form onFinish={handleCreateTeam} layout="vertical">
          <Form.Item name="team_name" label="名称" rules={[{required: true}]}>
            <Input style={{borderRadius: glacierTheme.borderRadius.md}}/>
          </Form.Item>
          <Form.Item name="domain" label="领域">
            <Input style={{borderRadius: glacierTheme.borderRadius.md}}/>
          </Form.Item>
          <AnimatedButton type="primary" htmlType="submit" block>
            创建
          </AnimatedButton>
        </Form>
      </Modal>

      {/* 邀请成员模态框 */}
      <Modal
        title={
          <span style={{fontSize: '18px', fontWeight: 600, color: glacierTheme.colors.text}}>
            邀请成员
          </span>
        }
        open={inviteModal.open}
        footer={null}
        onCancel={() => setInviteModal({open: false, teamId: null})}
        styles={{
          content: {
            background: glacierTheme.colors.background,
          },
        }}
      >
        <Form onFinish={handleInvite} layout="vertical">
          <Form.Item name="user_name" label="用户名" rules={[{required: true}]}>
            <Input style={{borderRadius: glacierTheme.borderRadius.md}}/>
          </Form.Item>
          <AnimatedButton type="primary" htmlType="submit" block>
            邀请
          </AnimatedButton>
        </Form>
      </Modal>

      {/* 项目详情模态框 */}
      <Modal
        title={
          <span style={{fontSize: '18px', fontWeight: 600, color: glacierTheme.colors.text}}>
            项目详情
          </span>
        }
        open={detailModal.open}
        onCancel={() => setDetailModal({open: false, data: null})}
        footer={null}
        width={700}
        styles={{
          content: {
            background: glacierTheme.colors.background,
          },
        }}
      >
        {detailModal.data && (
          <GlassCard style={{marginTop: glacierTheme.spacing.md}}>
            <Descriptions bordered column={1}>
              <Descriptions.Item label="名称">{detailModal.data.project_name}</Descriptions.Item>
              <Descriptions.Item label="负责人">{detailModal.data.principal_name}</Descriptions.Item>
              <Descriptions.Item label="状态">
                <Tag style={{
                  background: `${glacierTheme.colors.info}20`,
                  border: `1px solid ${glacierTheme.colors.info}`,
                  color: glacierTheme.colors.info,
                }}>
                  {detailModal.data.status}
                </Tag>
              </Descriptions.Item>

              {detailModal.data.review_info && detailModal.data.review_info.avg_score > 0 && (
                <Descriptions.Item label="复审结果">
                  <div style={{
                    padding: glacierTheme.spacing.lg,
                    background: `${glacierTheme.colors.success}15`,
                    border: `1px solid ${glacierTheme.colors.success}40`,
                    borderRadius: glacierTheme.borderRadius.md,
                  }}>
                    <div style={{marginBottom: glacierTheme.spacing.xs}}>
                      评审人评审均分：
                      <span style={{
                        fontSize: '24px',
                        fontWeight: 600,
                        color: glacierTheme.colors.success,
                        marginLeft: glacierTheme.spacing.xs,
                      }}>
                        {detailModal.data.review_info.avg_score}
                      </span>
                      分
                    </div>
                    <div style={{
                      color: glacierTheme.colors.textSecondary,
                      fontSize: '13px',
                      marginBottom: glacierTheme.spacing.md,
                    }}>
                      （基于 {detailModal.data.review_info.review_count} 位评审人的评分）
                    </div>
                    <div style={{fontWeight: 600}}>
                      {detailModal.data.review_info.avg_score > 60 ?
                        <span style={{color: glacierTheme.colors.success}}>✅ 分数达标，项目已通过复审。</span> :
                        <span style={{color: glacierTheme.colors.error}}>❌ 分数未达标 (需>60)，项目未通过。</span>
                      }
                    </div>
                  </div>
                </Descriptions.Item>
              )}

              <Descriptions.Item label="简介">{detailModal.data.project_description}</Descriptions.Item>
            </Descriptions>
          </GlassCard>
        )}
      </Modal>
    </div>
  );
};

export default UserDashboard;
