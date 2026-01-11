import React, {useState, useEffect} from 'react';
import {Tabs, Table, Tag, Modal, Form, Input, message, Descriptions, Space, Row, Col, Typography, Button, Progress, InputNumber, Steps, Select, DatePicker, List, Avatar, Empty} from 'antd';
import {ProjectOutlined, TeamOutlined, PlusOutlined, UserAddOutlined, FileTextOutlined, RocketOutlined, DollarOutlined, TrophyOutlined, CheckCircleOutlined, ClockCircleOutlined, PlayCircleOutlined, HandshakeOutlined, ShopOutlined, ApiOutlined, UserOutlined} from '@ant-design/icons';
import {useNavigate} from 'react-router-dom';
import dayjs from 'dayjs';
import {projectApi, teamApi, fundApi, milestoneApi, supporterApi} from '../../api/api';
import GlassCard from '../../components/GlassCard';
import AnimatedButton from '../../components/AnimatedButton';
import StatCard from '../../components/StatCard';
import AchievementList from '../../components/AchievementList';
import ResourceMarket from '../../components/ResourceMarket';
import {glacierTheme} from '../../styles/theme';

const {Title} = Typography;
const {TextArea} = Input;
const {Option} = Select;

const UserDashboard = () => {
  const navigate = useNavigate();
  const [projects, setProjects] = useState([]);
  const [myTeams, setMyTeams] = useState([]);
  const [teamModal, setTeamModal] = useState(false);
  const [inviteModal, setInviteModal] = useState({open: false, teamId: null});
  const [detailModal, setDetailModal] = useState({open: false, data: null});
  const [declareModal, setDeclareModal] = useState(false);
  const [expenditureModal, setExpenditureModal] = useState({open: false, projectId: null});
  const [milestoneModal, setMilestoneModal] = useState({open: false, milestone: null});
  const [intentionStatusModal, setIntentionStatusModal] = useState({open: false, intention: null});
  const [fundsData, setFundsData] = useState(null);
  const [milestones, setMilestones] = useState([]);
  const [intentions, setIntentions] = useState([]);
  const [form] = Form.useForm();
  const [expenditureForm] = Form.useForm();
  const [milestoneForm] = Form.useForm();
  const [intentionStatusForm] = Form.useForm();

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
    // 加载经费数据
    try {
      const fundsRes = await fundApi.getProjectFunds(id);
      setFundsData(fundsRes.data);
    } catch (e) {
      setFundsData(null);
    }
    // 加载里程碑数据
    try {
      const milestonesRes = await milestoneApi.getProjectMilestones(id);
      setMilestones(milestonesRes.data || []);
    } catch (e) {
      setMilestones([]);
    }
    // 加载对接意向数据（仅项目负责人可见）
    try {
      const intentionsRes = await supporterApi.getProjectIntentions(id);
      setIntentions(intentionsRes.data || []);
    } catch (e) {
      setIntentions([]);
    }
  };

  const handleSubmitExpenditure = async (values) => {
    try {
      await fundApi.submitExpenditure({
        project_id: expenditureModal.projectId,
        ...values,
        amount: parseFloat(values.amount),
      });
      message.success('报销提交成功');
      setExpenditureModal({open: false, projectId: null});
      expenditureForm.resetFields();
      // 重新加载经费数据
      if (detailModal.data) {
        const fundsRes = await fundApi.getProjectFunds(detailModal.data.project_id);
        setFundsData(fundsRes.data);
      }
    } catch (e) {
    }
  };

  const handleUpdateMilestone = async (values) => {
    try {
      await milestoneApi.updateMilestone(milestoneModal.milestone.milestone_id, {
        ...values,
        due_date: values.due_date ? values.due_date.format('YYYY-MM-DD') : null,
      });
      message.success('里程碑更新成功');
      setMilestoneModal({open: false, milestone: null});
      milestoneForm.resetFields();
      // 重新加载里程碑数据
      if (detailModal.data) {
        const milestonesRes = await milestoneApi.getProjectMilestones(detailModal.data.project_id);
        setMilestones(milestonesRes.data || []);
      }
    } catch (e) {
    }
  };

  const getMilestoneStatusIcon = (status) => {
    switch (status) {
      case '已完成':
        return <CheckCircleOutlined style={{color: glacierTheme.colors.success}}/>;
      case '进行中':
        return <PlayCircleOutlined style={{color: glacierTheme.colors.primary}}/>;
      default:
        return <ClockCircleOutlined style={{color: glacierTheme.colors.textLight}}/>;
    }
  };

  const getMilestoneStatusColor = (status) => {
    switch (status) {
      case '已完成':
        return glacierTheme.colors.success;
      case '进行中':
        return glacierTheme.colors.primary;
      default:
        return glacierTheme.colors.textLight;
    }
  };

  const handleUpdateIntentionStatus = async (values) => {
    try {
      await supporterApi.updateIntentionStatus(detailModal.data.project_id, {
        intention_id: intentionStatusModal.intention.intention_id,
        status: values.status,
      });
      message.success('对接意向状态更新成功');
      setIntentionStatusModal({open: false, intention: null});
      intentionStatusForm.resetFields();
      // 重新加载对接意向数据
      if (detailModal.data) {
        const intentionsRes = await supporterApi.getProjectIntentions(detailModal.data.project_id);
        setIntentions(intentionsRes.data || []);
      }
    } catch (e) {
      // 错误已在拦截器中处理
    }
  };

  const getSupportTypeIcon = (type) => {
    const iconMap = {
      '资金支持': <DollarOutlined/>,
      '产业资源': <ShopOutlined/>,
      '市场渠道': <ApiOutlined/>,
      '其他': <RocketOutlined/>,
    };
    return iconMap[type] || <RocketOutlined/>;
  };

  const getIntentionStatusColor = (status) => {
    switch (status) {
      case '已对接':
        return glacierTheme.colors.success;
      case '已婉拒':
        return glacierTheme.colors.error;
      default:
        return glacierTheme.colors.warning;
    }
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
            },
            {
              key: '3',
              label: (
                <span style={{fontSize: '15px', fontWeight: 500}}>
                  <ShopOutlined style={{marginRight: glacierTheme.spacing.xs}}/>
                  资源大厅
                </span>
              ),
              children: (
                <ResourceMarket/>
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
        onCancel={() => {
          setDetailModal({open: false, data: null});
          setFundsData(null);
        }}
        footer={null}
        width={700}
        styles={{
          content: {
            background: glacierTheme.colors.background,
          },
        }}
      >
        {detailModal.data && (
          <Tabs
            items={[
              {
                key: '1',
                label: '基本信息',
                children: (
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
                ),
              },
              {
                key: '2',
                label: '经费管理',
                children: (
                  <GlassCard style={{marginTop: glacierTheme.spacing.md}}>
                    {fundsData ? (
                      <div>
                        <div style={{
                          padding: glacierTheme.spacing.lg,
                          background: `${glacierTheme.colors.primary}10`,
                          border: `1px solid ${glacierTheme.colors.primary}30`,
                          borderRadius: glacierTheme.borderRadius.md,
                          marginBottom: glacierTheme.spacing.lg,
                        }}>
                          <Row gutter={[glacierTheme.spacing.md, glacierTheme.spacing.md]}>
                            <Col span={8}>
                              <div style={{textAlign: 'center'}}>
                                <div style={{
                                  fontSize: '14px',
                                  color: glacierTheme.colors.textSecondary,
                                  marginBottom: glacierTheme.spacing.xs,
                                }}>
                                  总经费
                                </div>
                                <div style={{
                                  fontSize: '20px',
                                  fontWeight: 600,
                                  color: glacierTheme.colors.primary,
                                }}>
                                  ¥{fundsData.total_funds.toFixed(2)}
                                </div>
                              </div>
                            </Col>
                            <Col span={8}>
                              <div style={{textAlign: 'center'}}>
                                <div style={{
                                  fontSize: '14px',
                                  color: glacierTheme.colors.textSecondary,
                                  marginBottom: glacierTheme.spacing.xs,
                                }}>
                                  已支出
                                </div>
                                <div style={{
                                  fontSize: '20px',
                                  fontWeight: 600,
                                  color: glacierTheme.colors.secondary,
                                }}>
                                  ¥{fundsData.total_expenditures.toFixed(2)}
                                </div>
                              </div>
                            </Col>
                            <Col span={8}>
                              <div style={{textAlign: 'center'}}>
                                <div style={{
                                  fontSize: '14px',
                                  color: glacierTheme.colors.textSecondary,
                                  marginBottom: glacierTheme.spacing.xs,
                                }}>
                                  余额
                                </div>
                                <div style={{
                                  fontSize: '20px',
                                  fontWeight: 600,
                                  color: fundsData.balance >= 0 ? glacierTheme.colors.success : glacierTheme.colors.error,
                                }}>
                                  ¥{fundsData.balance.toFixed(2)}
                                </div>
                              </div>
                            </Col>
                          </Row>
                        </div>

                        <div style={{marginBottom: glacierTheme.spacing.lg}}>
                          <div style={{
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'center',
                            marginBottom: glacierTheme.spacing.sm,
                          }}>
                            <span style={{color: glacierTheme.colors.text, fontWeight: 500}}>经费使用率</span>
                            <span style={{color: glacierTheme.colors.textSecondary, fontSize: '14px'}}>
                              {fundsData.usage_rate.toFixed(2)}%
                            </span>
                          </div>
                          <Progress
                            percent={fundsData.usage_rate}
                            strokeColor={{
                              '0%': glacierTheme.colors.primary,
                              '100%': fundsData.usage_rate > 80 ? glacierTheme.colors.error : glacierTheme.colors.secondary,
                            }}
                            showInfo={false}
                          />
                        </div>

                        <div style={{
                          display: 'flex',
                          justifyContent: 'flex-end',
                          marginTop: glacierTheme.spacing.lg,
                        }}>
                          <AnimatedButton
                            type="primary"
                            icon={<DollarOutlined/>}
                            onClick={() => setExpenditureModal({open: true, projectId: detailModal.data.project_id})}
                          >
                            申请报销
                          </AnimatedButton>
                        </div>
                      </div>
                    ) : (
                      <div style={{
                        textAlign: 'center',
                        padding: glacierTheme.spacing.xl,
                        color: glacierTheme.colors.textSecondary,
                      }}>
                        暂无经费数据
                      </div>
                    )}
                  </GlassCard>
                ),
              },
              {
                key: '3',
                label: '成果管理',
                icon: <TrophyOutlined/>,
                children: (
                  <div style={{marginTop: glacierTheme.spacing.md}}>
                    <AchievementList projectId={detailModal.data?.project_id}/>
                  </div>
                ),
              },
              {
                key: '4',
                label: '里程碑进度',
                icon: <RocketOutlined/>,
                children: (
                  <GlassCard style={{marginTop: glacierTheme.spacing.md}}>
                    {milestones.length === 0 ? (
                      <div style={{
                        textAlign: 'center',
                        padding: glacierTheme.spacing.xl,
                        color: glacierTheme.colors.textSecondary,
                      }}>
                        暂无里程碑数据
                      </div>
                    ) : (
                      <div>
                        <Steps
                          direction="vertical"
                          items={milestones.map((milestone, index) => ({
                            title: milestone.title,
                            description: (
                              <div>
                                <div style={{
                                  marginBottom: glacierTheme.spacing.xs,
                                  color: glacierTheme.colors.textSecondary,
                                  fontSize: '14px',
                                }}>
                                  {milestone.deliverable && (
                                    <div style={{marginBottom: glacierTheme.spacing.xs}}>
                                      <FileTextOutlined style={{marginRight: glacierTheme.spacing.xs}}/>
                                      {milestone.deliverable}
                                    </div>
                                  )}
                                  {milestone.due_date && (
                                    <div>
                                      <ClockCircleOutlined style={{marginRight: glacierTheme.spacing.xs}}/>
                                      截止日期：{new Date(milestone.due_date).toLocaleDateString('zh-CN')}
                                    </div>
                                  )}
                                </div>
                                {detailModal.data && (
                                  <Button
                                    type="link"
                                    size="small"
                                    onClick={() => {
                                      milestoneForm.setFieldsValue({
                                        status: milestone.status,
                                        deliverable: milestone.deliverable,
                                        due_date: milestone.due_date ? dayjs(milestone.due_date) : null,
                                      });
                                      setMilestoneModal({open: true, milestone});
                                    }}
                                    style={{
                                      padding: 0,
                                      color: glacierTheme.colors.primary,
                                    }}
                                  >
                                    更新状态
                                  </Button>
                                )}
                              </div>
                            ),
                            status: milestone.status === '已完成' ? 'finish' :
                                   milestone.status === '进行中' ? 'process' : 'wait',
                            icon: getMilestoneStatusIcon(milestone.status),
                          }))}
                        />
                      </div>
                    )}
                  </GlassCard>
                ),
              },
              {
                key: '5',
                label: '对接意向',
                icon: <TeamOutlined/>,
                children: (
                  <GlassCard style={{marginTop: glacierTheme.spacing.md}}>
                    {intentions.length === 0 ? (
                      <Empty
                        description="暂无对接意向"
                        image={Empty.PRESENTED_IMAGE_SIMPLE}
                        style={{
                          padding: glacierTheme.spacing.xl,
                          color: glacierTheme.colors.textSecondary,
                        }}
                      />
                    ) : (
                      <List
                        dataSource={intentions}
                        renderItem={(item) => (
                          <List.Item style={{padding: 0, marginBottom: glacierTheme.spacing.md}}>
                            <GlassCard
                              hoverable
                              style={{
                                width: '100%',
                                padding: glacierTheme.spacing.md,
                              }}
                            >
                              <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start'}}>
                                <div style={{flex: 1}}>
                                  <div style={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: glacierTheme.spacing.sm,
                                    marginBottom: glacierTheme.spacing.xs,
                                  }}>
                                    <Avatar
                                      icon={<UserOutlined/>}
                                      style={{
                                        background: glacierTheme.colors.primary,
                                      }}
                                    />
                                    <div>
                                      <Text strong style={{color: glacierTheme.colors.text, fontSize: '16px'}}>
                                        {item.supporter_name}
                                      </Text>
                                      {item.supporter_affiliation && (
                                        <Text style={{
                                          fontSize: '13px',
                                          color: glacierTheme.colors.textSecondary,
                                          marginLeft: glacierTheme.spacing.xs,
                                        }}>
                                          {item.supporter_affiliation}
                                        </Text>
                                      )}
                                    </div>
                                  </div>
                                  <div style={{
                                    marginTop: glacierTheme.spacing.xs,
                                    marginBottom: glacierTheme.spacing.xs,
                                  }}>
                                    <Tag
                                      icon={getSupportTypeIcon(item.support_type)}
                                      style={{
                                        background: `${glacierTheme.colors.primary}20`,
                                        border: `1px solid ${glacierTheme.colors.primary}`,
                                        color: glacierTheme.colors.primary,
                                      }}
                                    >
                                      {item.support_type}
                                    </Tag>
                                    <Tag style={{
                                      background: `${getIntentionStatusColor(item.status)}20`,
                                      border: `1px solid ${getIntentionStatusColor(item.status)}`,
                                      color: getIntentionStatusColor(item.status),
                                      marginLeft: glacierTheme.spacing.xs,
                                    }}>
                                      {item.status}
                                    </Tag>
                                  </div>
                                  {item.message && (
                                    <Paragraph style={{
                                      marginTop: glacierTheme.spacing.xs,
                                      marginBottom: 0,
                                      color: glacierTheme.colors.textSecondary,
                                    }}>
                                      {item.message}
                                    </Paragraph>
                                  )}
                                  {item.supporter_email && (
                                    <Text style={{
                                      fontSize: '12px',
                                      color: glacierTheme.colors.textLight,
                                      marginTop: glacierTheme.spacing.xs,
                                      display: 'block',
                                    }}>
                                      联系方式：{item.supporter_email}
                                    </Text>
                                  )}
                                  <Text style={{
                                    fontSize: '12px',
                                    color: glacierTheme.colors.textLight,
                                    marginTop: glacierTheme.spacing.xs,
                                    display: 'block',
                                  }}>
                                    提交时间：{new Date(item.create_time).toLocaleString('zh-CN')}
                                  </Text>
                                </div>
                                {detailModal.data && item.status === '待处理' && (
                                  <Button
                                    type="link"
                                    onClick={() => {
                                      intentionStatusForm.setFieldsValue({status: item.status});
                                      setIntentionStatusModal({open: true, intention: item});
                                    }}
                                    style={{color: glacierTheme.colors.primary}}
                                  >
                                    处理
                                  </Button>
                                )}
                              </div>
                            </GlassCard>
                          </List.Item>
                        )}
                      />
                    )}
                  </GlassCard>
                ),
              },
            ]}
          />
        )}
      </Modal>

      {/* 报销申请模态框 */}
      <Modal
        title={
          <span style={{fontSize: '18px', fontWeight: 600, color: glacierTheme.colors.text}}>
            申请报销
          </span>
        }
        open={expenditureModal.open}
        footer={null}
        onCancel={() => {
          setExpenditureModal({open: false, projectId: null});
          expenditureForm.resetFields();
        }}
        styles={{
          content: {
            background: glacierTheme.colors.background,
          },
        }}
      >
        <Form
          form={expenditureForm}
          onFinish={handleSubmitExpenditure}
          layout="vertical"
        >
          <Form.Item
            name="title"
            label="报销名目"
            rules={[{required: true, message: '请输入报销名目'}]}
          >
            <Input
              placeholder="例如：设备采购、差旅费、材料费等"
              style={{borderRadius: glacierTheme.borderRadius.md}}
            />
          </Form.Item>
          <Form.Item
            name="amount"
            label="报销金额"
            rules={[
              {required: true, message: '请输入报销金额'},
              {type: 'number', min: 0.01, message: '金额必须大于0'},
            ]}
          >
            <InputNumber
              prefix="¥"
              placeholder="0.00"
              style={{width: '100%', borderRadius: glacierTheme.borderRadius.md}}
              precision={2}
              min={0.01}
              step={0.01}
            />
          </Form.Item>
          {fundsData && (
            <div style={{
              padding: glacierTheme.spacing.md,
              background: `${glacierTheme.colors.info}10`,
              border: `1px solid ${glacierTheme.colors.info}30`,
              borderRadius: glacierTheme.borderRadius.md,
              marginBottom: glacierTheme.spacing.md,
            }}>
              <div style={{
                fontSize: '13px',
                color: glacierTheme.colors.textSecondary,
              }}>
                当前可用余额：<span style={{
                  color: glacierTheme.colors.primary,
                  fontWeight: 600,
                }}>¥{fundsData.balance.toFixed(2)}</span>
              </div>
            </div>
          )}
          <AnimatedButton type="primary" htmlType="submit" block>
            提交报销
          </AnimatedButton>
        </Form>
      </Modal>

      {/* 更新里程碑模态框 */}
      <Modal
        title={
          <span style={{fontSize: '18px', fontWeight: 600, color: glacierTheme.colors.text}}>
            更新里程碑
          </span>
        }
        open={milestoneModal.open}
        footer={null}
        onCancel={() => {
          setMilestoneModal({open: false, milestone: null});
          milestoneForm.resetFields();
        }}
        styles={{
          content: {
            background: glacierTheme.colors.background,
          },
        }}
      >
        <Form
          form={milestoneForm}
          onFinish={handleUpdateMilestone}
          layout="vertical"
        >
          <Form.Item
            name="status"
            label="状态"
            rules={[{required: true, message: '请选择状态'}]}
          >
            <Select
              placeholder="选择里程碑状态"
              style={{borderRadius: glacierTheme.borderRadius.md}}
            >
              <Option value="未开始">未开始</Option>
              <Option value="进行中">进行中</Option>
              <Option value="已完成">已完成</Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="deliverable"
            label="交付物描述"
          >
            <TextArea
              rows={3}
              placeholder="描述此里程碑需要交付的内容"
              style={{borderRadius: glacierTheme.borderRadius.md}}
            />
          </Form.Item>

          <Form.Item
            name="due_date"
            label="截止日期"
          >
            <DatePicker
              style={{width: '100%', borderRadius: glacierTheme.borderRadius.md}}
              format="YYYY-MM-DD"
              placeholder="选择截止日期"
            />
          </Form.Item>

          <Form.Item style={{marginBottom: 0, marginTop: glacierTheme.spacing.lg}}>
            <Space style={{width: '100%', justifyContent: 'flex-end'}}>
              <Button
                onClick={() => {
                  setMilestoneModal({open: false, milestone: null});
                  milestoneForm.resetFields();
                }}
                style={{borderRadius: glacierTheme.borderRadius.md}}
              >
                取消
              </Button>
              <AnimatedButton type="primary" htmlType="submit">
                更新
              </AnimatedButton>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 更新对接意向状态模态框 */}
      <Modal
        title={
          <span style={{fontSize: '18px', fontWeight: 600, color: glacierTheme.colors.text}}>
            处理对接意向
          </span>
        }
        open={intentionStatusModal.open}
        footer={null}
        onCancel={() => {
          setIntentionStatusModal({open: false, intention: null});
          intentionStatusForm.resetFields();
        }}
        styles={{
          content: {
            background: glacierTheme.colors.background,
          },
        }}
      >
        {intentionStatusModal.intention && (
          <div style={{marginBottom: glacierTheme.spacing.lg}}>
            <div style={{marginBottom: glacierTheme.spacing.sm}}>
              <Text style={{color: glacierTheme.colors.textSecondary}}>支持者：</Text>
              <Text strong style={{color: glacierTheme.colors.text, marginLeft: glacierTheme.spacing.xs}}>
                {intentionStatusModal.intention.supporter_name}
              </Text>
            </div>
            <div style={{marginBottom: glacierTheme.spacing.sm}}>
              <Text style={{color: glacierTheme.colors.textSecondary}}>支持类型：</Text>
              <Tag style={{marginLeft: glacierTheme.spacing.xs}}>
                {getSupportTypeIcon(intentionStatusModal.intention.support_type)}
                {' '}
                {intentionStatusModal.intention.support_type}
              </Tag>
            </div>
            {intentionStatusModal.intention.message && (
              <div style={{
                padding: glacierTheme.spacing.md,
                background: glacierTheme.colors.surface,
                borderRadius: glacierTheme.borderRadius.md,
                marginBottom: glacierTheme.spacing.md,
              }}>
                <Text style={{color: glacierTheme.colors.textSecondary}}>留言：</Text>
                <Paragraph style={{marginTop: glacierTheme.spacing.xs, marginBottom: 0}}>
                  {intentionStatusModal.intention.message}
                </Paragraph>
              </div>
            )}
          </div>
        )}
        <Form
          form={intentionStatusForm}
          layout="vertical"
          onFinish={handleUpdateIntentionStatus}
        >
          <Form.Item
            name="status"
            label="处理状态"
            rules={[{required: true, message: '请选择处理状态'}]}
          >
            <Select
              placeholder="选择处理状态"
              style={{borderRadius: glacierTheme.borderRadius.md}}
            >
              <Option value="待处理">待处理</Option>
              <Option value="已对接">已对接</Option>
              <Option value="已婉拒">已婉拒</Option>
            </Select>
          </Form.Item>

          <Form.Item style={{marginBottom: 0, marginTop: glacierTheme.spacing.lg}}>
            <Space style={{width: '100%', justifyContent: 'flex-end'}}>
              <Button
                onClick={() => {
                  setIntentionStatusModal({open: false, intention: null});
                  intentionStatusForm.resetFields();
                }}
                style={{borderRadius: glacierTheme.borderRadius.md}}
              >
                取消
              </Button>
              <AnimatedButton type="primary" htmlType="submit">
                更新
              </AnimatedButton>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default UserDashboard;
