import React, {useState, useEffect} from 'react';
import {Card, Steps, Form, Input, DatePicker, InputNumber, Button, message, Modal, Timeline, Tag, Typography, Space, Divider, Row, Col, Progress} from 'antd';
import dayjs from 'dayjs';
import {RocketOutlined, CheckCircleOutlined, ClockCircleOutlined, FileTextOutlined, PlusOutlined, EditOutlined} from '@ant-design/icons';
import {useNavigate, useParams} from 'react-router-dom';
import {incubationApi, pocApi, projectApi} from '../../api/api';
import GlassCard from '../../components/GlassCard';
import AnimatedButton from '../../components/AnimatedButton';
import {glacierTheme} from '../../styles/theme';

const {Title, Text, Paragraph} = Typography;
const {TextArea} = Input;

const IncubationDashboard = () => {
  const {projectId} = useParams();
  const navigate = useNavigate();
  const [incubation, setIncubation] = useState(null);
  const [pocs, setPocs] = useState([]);
  const [project, setProject] = useState(null);
  const [planModal, setPlanModal] = useState(false);
  const [pocModal, setPocModal] = useState({open: false, poc: null});
  const [form] = Form.useForm();
  const [pocForm] = Form.useForm();
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (projectId) {
      loadData();
    }
  }, [projectId]);

  const loadData = async () => {
    try {
      setLoading(true);
      const [incubationRes, pocsRes, projectRes] = await Promise.all([
        incubationApi.get(projectId),
        pocApi.getList(projectId),
        projectApi.getDetail(projectId),
      ]);
      
      if (incubationRes.data && incubationRes.data.incubation) {
        setIncubation(incubationRes.data.incubation);
      }
      setPocs(pocsRes.data);
      setProject(projectRes.data);
    } catch (e) {
      message.error('加载数据失败');
    } finally {
      setLoading(false);
    }
  };

  const handleSavePlan = async (values) => {
    try {
      const submitData = {
        incubation_plan: values.incubation_plan || '',
        resources: values.resources || '',
        challenges: values.challenges || '',
        achievements: values.achievements || '',
        milestones: values.milestones || [],
        progress: values.progress || 0,
      };
      
      if (values.planned_end_time) {
        submitData.planned_end_time = values.planned_end_time.format('YYYY-MM-DD');
      }
      
      await incubationApi.createOrUpdate(projectId, submitData);
      message.success('孵化计划保存成功');
      setPlanModal(false);
      form.resetFields();
      loadData();
    } catch (e) {
      const errorMsg = e.response?.data?.message || '保存失败，请重试';
      message.error(errorMsg);
    }
  };

  const handleCreatePoc = async (values) => {
    try {
      await pocApi.create(projectId, values);
      message.success('概念验证记录创建成功');
      setPocModal({open: false, poc: null});
      pocForm.resetFields();
      loadData();
    } catch (e) {
    }
  };

  const getStatusColor = (status) => {
    const colors = {
      '计划中': glacierTheme.colors.info,
      '进行中': glacierTheme.colors.primary,
      '已完成': glacierTheme.colors.success,
      '已验证': glacierTheme.colors.success,
      '待开始': glacierTheme.colors.textSecondary,
      '未通过': glacierTheme.colors.error,
    };
    return colors[status] || glacierTheme.colors.textSecondary;
  };

  const getStatusStep = () => {
    if (!incubation) return 0;
    if (incubation.status === '已完成') return 3;
    if (pocs.some(p => p.status === '已验证')) return 2;
    if (incubation.status === '进行中') return 1;
    return 0;
  };

  if (!project) {
    return <div>加载中...</div>;
  }

  if (project.status !== '已通过' && project.status !== '孵化中' && project.status !== '概念验证中') {
    return (
      <GlassCard>
        <div style={{textAlign: 'center', padding: glacierTheme.spacing.xl}}>
          <Text style={{fontSize: '16px', color: glacierTheme.colors.textSecondary}}>
            该项目尚未通过复审，无法进行孵化
          </Text>
        </div>
      </GlassCard>
    );
  }

  return (
    <div style={{display: 'flex', flexDirection: 'column', gap: glacierTheme.spacing.xl}}>
      {/* 项目信息卡片 */}
      <GlassCard>
        <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: glacierTheme.spacing.md}}>
          <div>
            <Title level={3} style={{margin: 0, marginBottom: glacierTheme.spacing.sm, color: glacierTheme.colors.text}}>
              {project.project_name}
            </Title>
            <Space>
              <Tag style={{
                background: `${glacierTheme.colors.success}20`,
                border: `1px solid ${glacierTheme.colors.success}`,
                color: glacierTheme.colors.success,
              }}>
                {project.status}
              </Tag>
              <Text style={{color: glacierTheme.colors.textSecondary}}>领域：{project.domain}</Text>
            </Space>
          </div>
          <AnimatedButton
            icon={<RocketOutlined/>}
            onClick={() => navigate('/dashboard')}
            style={{
              border: `1px solid ${glacierTheme.colors.border}`,
              background: glacierTheme.colors.surface,
            }}
          >
            返回项目列表
          </AnimatedButton>
        </div>
      </GlassCard>

      {/* 孵化进度 */}
      <GlassCard>
        <div style={{marginBottom: glacierTheme.spacing.lg}}>
          <Title level={4} style={{margin: 0, color: glacierTheme.colors.text, fontWeight: 600}}>
            孵化进度
          </Title>
        </div>
        <Steps
          current={getStatusStep()}
          items={[
            {title: '复审通过', icon: <CheckCircleOutlined/>},
            {title: '孵化中', icon: <ClockCircleOutlined/>},
            {title: '概念验证', icon: <FileTextOutlined/>},
            {title: '孵化完成', icon: <CheckCircleOutlined/>},
          ]}
        />
        {incubation && (
          <div style={{marginTop: glacierTheme.spacing.lg}}>
            <div style={{marginBottom: glacierTheme.spacing.md}}>
              <Text style={{color: glacierTheme.colors.textSecondary}}>整体进度</Text>
              <Progress
                percent={incubation.progress}
                strokeColor={glacierTheme.colors.primary}
                style={{marginTop: glacierTheme.spacing.xs}}
              />
            </div>
            <Row gutter={[glacierTheme.spacing.lg, glacierTheme.spacing.md]}>
              <Col xs={24} sm={12}>
                <Text style={{color: glacierTheme.colors.textSecondary}}>开始时间：</Text>
                <Text>{new Date(incubation.start_time).toLocaleDateString()}</Text>
              </Col>
              <Col xs={24} sm={12}>
                <Text style={{color: glacierTheme.colors.textSecondary}}>计划结束：</Text>
                <Text>
                  {incubation.planned_end_time 
                    ? new Date(incubation.planned_end_time).toLocaleDateString()
                    : '未设置'}
                </Text>
              </Col>
            </Row>
          </div>
        )}
      </GlassCard>

      {/* 孵化计划 */}
      <GlassCard>
        <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: glacierTheme.spacing.lg}}>
          <Title level={4} style={{margin: 0, color: glacierTheme.colors.text, fontWeight: 600}}>
            孵化计划
          </Title>
          <AnimatedButton
            type="primary"
            icon={incubation ? <EditOutlined/> : <PlusOutlined/>}
            onClick={() => {
              if (incubation) {
                form.setFieldsValue({
                  incubation_plan: incubation.incubation_plan,
                  resources: incubation.resources,
                  planned_end_time: incubation.planned_end_time ? dayjs(incubation.planned_end_time) : null,
                  milestones: incubation.milestones || [],
                  progress: incubation.progress,
                  challenges: incubation.challenges,
                  achievements: incubation.achievements,
                });
              }
              setPlanModal(true);
            }}
          >
            {incubation ? '编辑计划' : '创建计划'}
          </AnimatedButton>
        </div>
        {incubation ? (
          <div>
            {incubation.incubation_plan && (
              <div style={{marginBottom: glacierTheme.spacing.lg}}>
                <Text strong style={{color: glacierTheme.colors.text}}>计划内容：</Text>
                <Paragraph style={{marginTop: glacierTheme.spacing.xs, color: glacierTheme.colors.textSecondary}}>
                  {incubation.incubation_plan}
                </Paragraph>
              </div>
            )}
            {incubation.resources && (
              <div style={{marginBottom: glacierTheme.spacing.lg}}>
                <Text strong style={{color: glacierTheme.colors.text}}>资源需求：</Text>
                <Paragraph style={{marginTop: glacierTheme.spacing.xs, color: glacierTheme.colors.textSecondary}}>
                  {incubation.resources}
                </Paragraph>
              </div>
            )}
            {incubation.achievements && (
              <div style={{marginBottom: glacierTheme.spacing.lg}}>
                <Text strong style={{color: glacierTheme.colors.text}}>取得的成果：</Text>
                <Paragraph style={{marginTop: glacierTheme.spacing.xs, color: glacierTheme.colors.textSecondary}}>
                  {incubation.achievements}
                </Paragraph>
              </div>
            )}
            {incubation.challenges && (
              <div>
                <Text strong style={{color: glacierTheme.colors.text}}>面临的挑战：</Text>
                <Paragraph style={{marginTop: glacierTheme.spacing.xs, color: glacierTheme.colors.textSecondary}}>
                  {incubation.challenges}
                </Paragraph>
              </div>
            )}
          </div>
        ) : (
          <div style={{textAlign: 'center', padding: glacierTheme.spacing.xl}}>
            <Text style={{color: glacierTheme.colors.textSecondary}}>尚未创建孵化计划</Text>
          </div>
        )}
      </GlassCard>

      {/* 概念验证记录 */}
      <GlassCard>
        <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: glacierTheme.spacing.lg}}>
          <Title level={4} style={{margin: 0, color: glacierTheme.colors.text, fontWeight: 600}}>
            概念验证记录
          </Title>
          <AnimatedButton
            type="primary"
            icon={<PlusOutlined/>}
            onClick={() => {
              pocForm.resetFields();
              setPocModal({open: true, poc: null});
            }}
          >
            新建验证
          </AnimatedButton>
        </div>
        {pocs.length > 0 ? (
          <Timeline>
            {pocs.map((poc) => (
              <Timeline.Item
                key={poc.poc_id}
                color={getStatusColor(poc.status)}
                dot={poc.status === '已验证' ? <CheckCircleOutlined/> : <FileTextOutlined/>}
              >
                <div style={{
                  background: glacierTheme.colors.surface,
                  padding: glacierTheme.spacing.md,
                  borderRadius: glacierTheme.borderRadius.md,
                  marginBottom: glacierTheme.spacing.md,
                }}>
                  <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: glacierTheme.spacing.xs}}>
                    <Title level={5} style={{margin: 0, color: glacierTheme.colors.text}}>
                      {poc.title}
                    </Title>
                    <Tag style={{
                      background: `${getStatusColor(poc.status)}20`,
                      border: `1px solid ${getStatusColor(poc.status)}`,
                      color: getStatusColor(poc.status),
                    }}>
                      {poc.status}
                    </Tag>
                  </div>
                  {poc.description && (
                    <Paragraph style={{color: glacierTheme.colors.textSecondary, marginBottom: glacierTheme.spacing.xs}}>
                      {poc.description}
                    </Paragraph>
                  )}
                  {poc.verification_objective && (
                    <div style={{marginTop: glacierTheme.spacing.xs}}>
                      <Text strong style={{color: glacierTheme.colors.text}}>验证目标：</Text>
                      <Text style={{color: glacierTheme.colors.textSecondary, marginLeft: glacierTheme.spacing.xs}}>
                        {poc.verification_objective}
                      </Text>
                    </div>
                  )}
                  {poc.conclusion && (
                    <div style={{marginTop: glacierTheme.spacing.xs}}>
                      <Text strong style={{color: glacierTheme.colors.text}}>结论：</Text>
                      <Text style={{color: glacierTheme.colors.textSecondary, marginLeft: glacierTheme.spacing.xs}}>
                        {poc.conclusion}
                      </Text>
                    </div>
                  )}
                </div>
              </Timeline.Item>
            ))}
          </Timeline>
        ) : (
          <div style={{textAlign: 'center', padding: glacierTheme.spacing.xl}}>
            <Text style={{color: glacierTheme.colors.textSecondary}}>暂无概念验证记录</Text>
          </div>
        )}
      </GlassCard>

      {/* 孵化计划模态框 */}
      <Modal
        title={<span style={{fontSize: '18px', fontWeight: 600, color: glacierTheme.colors.text}}>
          {incubation ? '编辑孵化计划' : '创建孵化计划'}
        </span>}
        open={planModal}
        footer={null}
        onCancel={() => {
          setPlanModal(false);
          form.resetFields();
        }}
        width={700}
        styles={{
          content: {
            background: glacierTheme.colors.background,
          },
        }}
      >
        <Form form={form} onFinish={handleSavePlan} layout="vertical">
          <Form.Item name="incubation_plan" label="孵化计划" rules={[{required: true, message: '请输入孵化计划'}]}>
            <TextArea rows={6} placeholder="详细描述项目的孵化计划..." style={{borderRadius: glacierTheme.borderRadius.md}}/>
          </Form.Item>
          <Form.Item name="resources" label="资源需求">
            <TextArea rows={4} placeholder="描述项目孵化所需的资源..." style={{borderRadius: glacierTheme.borderRadius.md}}/>
          </Form.Item>
          <Form.Item name="planned_end_time" label="计划结束时间">
            <DatePicker style={{width: '100%', borderRadius: glacierTheme.borderRadius.md}}/>
          </Form.Item>
          <Form.Item name="progress" label="当前进度（%）">
            <InputNumber min={0} max={100} style={{width: '100%'}}/>
          </Form.Item>
          <Form.Item name="achievements" label="取得的成果">
            <TextArea rows={3} placeholder="描述项目孵化过程中取得的成果..." style={{borderRadius: glacierTheme.borderRadius.md}}/>
          </Form.Item>
          <Form.Item name="challenges" label="面临的挑战">
            <TextArea rows={3} placeholder="描述项目孵化过程中面临的挑战..." style={{borderRadius: glacierTheme.borderRadius.md}}/>
          </Form.Item>
          <AnimatedButton type="primary" htmlType="submit" block>
            保存
          </AnimatedButton>
        </Form>
      </Modal>

      {/* 概念验证模态框 */}
      <Modal
        title={<span style={{fontSize: '18px', fontWeight: 600, color: glacierTheme.colors.text}}>
          新建概念验证
        </span>}
        open={pocModal.open}
        footer={null}
        onCancel={() => {
          setPocModal({open: false, poc: null});
          pocForm.resetFields();
        }}
        width={700}
        styles={{
          content: {
            background: glacierTheme.colors.background,
          },
        }}
      >
        <Form form={pocForm} onFinish={handleCreatePoc} layout="vertical">
          <Form.Item name="title" label="验证标题" rules={[{required: true, message: '请输入验证标题'}]}>
            <Input style={{borderRadius: glacierTheme.borderRadius.md}}/>
          </Form.Item>
          <Form.Item name="description" label="验证描述">
            <TextArea rows={4} placeholder="描述本次概念验证的内容..." style={{borderRadius: glacierTheme.borderRadius.md}}/>
          </Form.Item>
          <Form.Item name="verification_objective" label="验证目标">
            <TextArea rows={3} placeholder="描述本次验证的目标..." style={{borderRadius: glacierTheme.borderRadius.md}}/>
          </Form.Item>
          <Form.Item name="verification_method" label="验证方法">
            <TextArea rows={3} placeholder="描述验证采用的方法..." style={{borderRadius: glacierTheme.borderRadius.md}}/>
          </Form.Item>
          <AnimatedButton type="primary" htmlType="submit" block>
            创建
          </AnimatedButton>
        </Form>
      </Modal>
    </div>
  );
};

export default IncubationDashboard;
