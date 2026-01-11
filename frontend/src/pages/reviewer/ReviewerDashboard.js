import React, {useState, useEffect} from 'react';
import {List, Button, Drawer, Input, Slider, message, Tag, Empty, Row, Col, Typography} from 'antd';
import {FormOutlined, CheckCircleOutlined, ClockCircleOutlined, RocketOutlined} from '@ant-design/icons';
import {useNavigate} from 'react-router-dom';
import {reviewApi} from '../../api/api';
import GlassCard from '../../components/GlassCard';
import AnimatedButton from '../../components/AnimatedButton';
import StatCard from '../../components/StatCard';
import {glacierTheme} from '../../styles/theme';

const {Title, Text} = Typography;

const ReviewerDashboard = () => {
  const navigate = useNavigate();
  const [tasks, setTasks] = useState([]);
  const [incubationProjects, setIncubationProjects] = useState([]);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [currentTask, setCurrentTask] = useState(null);
  const [reviewData, setReviewData] = useState({
    innovation: 20,
    feasibility: 20,
    teamwork: 20,
    potentiality: 20,
    comment: ''
  });

  useEffect(() => {
    loadTasks();
    loadIncubationProjects();
  }, []);

  const loadTasks = async () => {
    try {
      const res = await reviewApi.getMyTasks();
      setTasks(res.data);
    } catch (e) {
    }
  };

  const loadIncubationProjects = async () => {
    try {
      const res = await reviewApi.getIncubationProjects();
      setIncubationProjects(res.data || []);
    } catch (e) {
      // 如果接口不存在或失败，静默处理
      setIncubationProjects([]);
    }
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
      setReviewData({
        innovation: 20,
        feasibility: 20,
        teamwork: 20,
        potentiality: 20,
        comment: ''
      });
      loadTasks();
    } catch (e) {
    }
  };

  const pendingCount = tasks.filter(t => t.status !== '已完成').length;
  const completedCount = tasks.filter(t => t.status === '已完成').length;

  const getStatusColor = (status) => {
    switch (status) {
      case '孵化中':
        return glacierTheme.colors.primary;
      case '概念验证中':
        return glacierTheme.colors.warning;
      case '孵化完成':
        return glacierTheme.colors.success;
      default:
        return glacierTheme.colors.textSecondary;
    }
  };

  return (
    <div style={{display: 'flex', flexDirection: 'column', gap: glacierTheme.spacing.xl}}>
      {/* 统计卡片 */}
      <Row gutter={[glacierTheme.spacing.lg, glacierTheme.spacing.lg]}>
        <Col xs={24} sm={12} lg={6}>
          <StatCard
            title="待评审任务"
            value={pendingCount}
            icon={<ClockCircleOutlined/>}
            color="warning"
          />
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <StatCard
            title="已完成任务"
            value={completedCount}
            icon={<CheckCircleOutlined/>}
            color="success"
          />
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <StatCard
            title="总任务数"
            value={tasks.length}
            icon={<FormOutlined/>}
            color="info"
          />
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <StatCard
            title="孵化项目"
            value={incubationProjects.length}
            icon={<RocketOutlined/>}
            color="primary"
          />
        </Col>
      </Row>

      {/* 任务列表 */}
      <GlassCard>
        <Title level={4} style={{
          margin: 0,
          marginBottom: glacierTheme.spacing.lg,
          color: glacierTheme.colors.text,
          fontWeight: 600,
        }}>
          我的评审任务
        </Title>
        <List
          dataSource={tasks}
          locale={{emptyText: <Empty description="暂无任务"/>}}
          renderItem={(item) => (
            <List.Item
              style={{
                padding: glacierTheme.spacing.lg,
                marginBottom: glacierTheme.spacing.md,
                borderRadius: glacierTheme.borderRadius.md,
                background: glacierTheme.colors.surface,
                border: `1px solid ${glacierTheme.colors.border}`,
                transition: `all ${glacierTheme.transitions.fast}`,
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = glacierTheme.colors.surfaceHover;
                e.currentTarget.style.transform = 'translateX(4px)';
                e.currentTarget.style.boxShadow = glacierTheme.shadows.md;
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = glacierTheme.colors.surface;
                e.currentTarget.style.transform = 'translateX(0)';
                e.currentTarget.style.boxShadow = 'none';
              }}
            >
              <List.Item.Meta
                avatar={
                  <div style={{
                    width: 48,
                    height: 48,
                    borderRadius: glacierTheme.borderRadius.md,
                    background: `linear-gradient(135deg, ${glacierTheme.colors.primaryLight} 0%, ${glacierTheme.colors.primary} 100%)`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '24px',
                    color: '#fff',
                  }}>
                    <FormOutlined/>
                  </div>
                }
                title={
                  <span style={{
                    fontSize: '16px',
                    fontWeight: 600,
                    color: glacierTheme.colors.text,
                  }}>
                    {item.project_name}
                  </span>
                }
                description={
                  <div style={{
                    color: glacierTheme.colors.textSecondary,
                    fontSize: '14px',
                    marginTop: glacierTheme.spacing.xs,
                  }}>
                    <span>领域：{item.domain}</span>
                    <span style={{margin: `0 ${glacierTheme.spacing.md}`}}>|</span>
                    <span>截止：{item.deadline}</span>
                  </div>
                }
              />
              <div>
                {item.status === '已完成' ? (
                  <Tag color={glacierTheme.colors.success} style={{
                    padding: `${glacierTheme.spacing.xs} ${glacierTheme.spacing.md}`,
                    borderRadius: glacierTheme.borderRadius.md,
                    border: 'none',
                  }}>
                    已提交
                  </Tag>
                ) : (
                  <AnimatedButton
                    type="primary"
                    onClick={() => openReview(item)}
                    style={{
                      borderRadius: glacierTheme.borderRadius.md,
                    }}
                  >
                    开始评审
                  </AnimatedButton>
                )}
              </div>
            </List.Item>
          )}
        />
      </GlassCard>

      {/* 孵化项目列表 */}
      {incubationProjects.length > 0 && (
        <GlassCard>
          <Title level={4} style={{
            margin: 0,
            marginBottom: glacierTheme.spacing.lg,
            color: glacierTheme.colors.text,
            fontWeight: 600,
          }}>
            我评审的孵化项目
          </Title>
          <List
            dataSource={incubationProjects}
            locale={{emptyText: <Empty description="暂无孵化项目"/>}}
            renderItem={(item) => (
              <List.Item
                style={{
                  padding: glacierTheme.spacing.lg,
                  marginBottom: glacierTheme.spacing.md,
                  borderRadius: glacierTheme.borderRadius.md,
                  background: glacierTheme.colors.surface,
                  border: `1px solid ${glacierTheme.colors.border}`,
                  transition: `all ${glacierTheme.transitions.fast}`,
                  cursor: 'pointer',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = glacierTheme.colors.surfaceHover;
                  e.currentTarget.style.transform = 'translateX(4px)';
                  e.currentTarget.style.boxShadow = glacierTheme.shadows.md;
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = glacierTheme.colors.surface;
                  e.currentTarget.style.transform = 'translateX(0)';
                  e.currentTarget.style.boxShadow = 'none';
                }}
                onClick={() => navigate(`/incubation/${item.project_id}`)}
              >
                <List.Item.Meta
                  avatar={
                    <div style={{
                      width: 48,
                      height: 48,
                      borderRadius: glacierTheme.borderRadius.md,
                      background: `linear-gradient(135deg, ${getStatusColor(item.status)}40 0%, ${getStatusColor(item.status)} 100%)`,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '24px',
                      color: '#fff',
                    }}>
                      <RocketOutlined/>
                    </div>
                  }
                  title={
                    <span style={{
                      fontSize: '16px',
                      fontWeight: 600,
                      color: glacierTheme.colors.text,
                    }}>
                      {item.project_name}
                    </span>
                  }
                  description={
                    <div style={{
                      color: glacierTheme.colors.textSecondary,
                      fontSize: '14px',
                      marginTop: glacierTheme.spacing.xs,
                    }}>
                      <span>领域：{item.domain}</span>
                      <span style={{margin: `0 ${glacierTheme.spacing.md}`}}>|</span>
                      <span>负责人：{item.principal_name}</span>
                      <span style={{margin: `0 ${glacierTheme.spacing.md}`}}>|</span>
                      <span>成熟度：{item.maturity_level}</span>
                    </div>
                  }
                />
                <div>
                  <Tag
                    style={{
                      background: `${getStatusColor(item.status)}20`,
                      border: `1px solid ${getStatusColor(item.status)}`,
                      color: getStatusColor(item.status),
                      padding: `${glacierTheme.spacing.xs} ${glacierTheme.spacing.md}`,
                      borderRadius: glacierTheme.borderRadius.md,
                    }}
                  >
                    {item.status}
                  </Tag>
                  <AnimatedButton
                    type="link"
                    onClick={(e) => {
                      e.stopPropagation();
                      navigate(`/incubation/${item.project_id}`);
                    }}
                    style={{
                      marginLeft: glacierTheme.spacing.md,
                      color: glacierTheme.colors.primary,
                    }}
                  >
                    查看详情
                  </AnimatedButton>
                </div>
              </List.Item>
            )}
          />
        </GlassCard>
      )}

      {/* 评审抽屉 */}
      <Drawer
        title={
          <span style={{
            fontSize: '18px',
            fontWeight: 600,
            color: glacierTheme.colors.text,
          }}>
            项目评审
          </span>
        }
        width={520}
        onClose={() => setDrawerOpen(false)}
        open={drawerOpen}
        footer={
          <AnimatedButton
            type="primary"
            block
            onClick={handleSubmitReview}
            style={{
              height: '44px',
              fontSize: '16px',
            }}
          >
            提交评审
          </AnimatedButton>
        }
        styles={{
          body: {
            background: glacierTheme.colors.background,
          },
        }}
      >
        <div style={{marginBottom: glacierTheme.spacing.xl}}>
          <div style={{
            marginBottom: glacierTheme.spacing.md,
            color: glacierTheme.colors.text,
            fontWeight: 500,
          }}>
            创新性 (30分)
          </div>
          <Slider
            max={30}
            value={reviewData.innovation}
            onChange={v => setReviewData({...reviewData, innovation: v})}
            trackStyle={{background: glacierTheme.colors.primary}}
            handleStyle={{borderColor: glacierTheme.colors.primary}}
          />
          <div style={{
            textAlign: 'right',
            color: glacierTheme.colors.textSecondary,
            fontSize: '12px',
            marginTop: glacierTheme.spacing.xs,
          }}>
            {reviewData.innovation} 分
          </div>
        </div>

        <div style={{marginBottom: glacierTheme.spacing.xl}}>
          <div style={{
            marginBottom: glacierTheme.spacing.md,
            color: glacierTheme.colors.text,
            fontWeight: 500,
          }}>
            可行性 (30分)
          </div>
          <Slider
            max={30}
            value={reviewData.feasibility}
            onChange={v => setReviewData({...reviewData, feasibility: v})}
            trackStyle={{background: glacierTheme.colors.primary}}
            handleStyle={{borderColor: glacierTheme.colors.primary}}
          />
          <div style={{
            textAlign: 'right',
            color: glacierTheme.colors.textSecondary,
            fontSize: '12px',
            marginTop: glacierTheme.spacing.xs,
          }}>
            {reviewData.feasibility} 分
          </div>
        </div>

        <div style={{marginBottom: glacierTheme.spacing.xl}}>
          <div style={{
            marginBottom: glacierTheme.spacing.md,
            color: glacierTheme.colors.text,
            fontWeight: 500,
          }}>
            团队能力 (20分)
          </div>
          <Slider
            max={20}
            value={reviewData.teamwork}
            onChange={v => setReviewData({...reviewData, teamwork: v})}
            trackStyle={{background: glacierTheme.colors.primary}}
            handleStyle={{borderColor: glacierTheme.colors.primary}}
          />
          <div style={{
            textAlign: 'right',
            color: glacierTheme.colors.textSecondary,
            fontSize: '12px',
            marginTop: glacierTheme.spacing.xs,
          }}>
            {reviewData.teamwork} 分
          </div>
        </div>

        <div style={{marginBottom: glacierTheme.spacing.xl}}>
          <div style={{
            marginBottom: glacierTheme.spacing.md,
            color: glacierTheme.colors.text,
            fontWeight: 500,
          }}>
            潜力 (20分)
          </div>
          <Slider
            max={20}
            value={reviewData.potentiality}
            onChange={v => setReviewData({...reviewData, potentiality: v})}
            trackStyle={{background: glacierTheme.colors.primary}}
            handleStyle={{borderColor: glacierTheme.colors.primary}}
          />
          <div style={{
            textAlign: 'right',
            color: glacierTheme.colors.textSecondary,
            fontSize: '12px',
            marginTop: glacierTheme.spacing.xs,
          }}>
            {reviewData.potentiality} 分
          </div>
        </div>

        <div>
          <div style={{
            marginBottom: glacierTheme.spacing.md,
            color: glacierTheme.colors.text,
            fontWeight: 500,
          }}>
            评审意见
          </div>
          <Input.TextArea
            rows={6}
            placeholder="请输入评审意见..."
            value={reviewData.comment}
            onChange={e => setReviewData({...reviewData, comment: e.target.value})}
            style={{
              borderRadius: glacierTheme.borderRadius.md,
              border: `1px solid ${glacierTheme.colors.border}`,
            }}
          />
        </div>

        <div style={{
          marginTop: glacierTheme.spacing.xl,
          padding: glacierTheme.spacing.md,
          borderRadius: glacierTheme.borderRadius.md,
          background: glacierTheme.colors.surface,
          textAlign: 'center',
        }}>
          <div style={{
            color: glacierTheme.colors.textSecondary,
            fontSize: '14px',
            marginBottom: glacierTheme.spacing.xs,
          }}>
            总分
          </div>
          <div style={{
            fontSize: '32px',
            fontWeight: 600,
            color: glacierTheme.colors.primary,
          }}>
            {reviewData.innovation + reviewData.feasibility + reviewData.teamwork + reviewData.potentiality} 分
          </div>
        </div>
      </Drawer>
    </div>
  );
};

export default ReviewerDashboard;
