import React, {useState, useEffect} from 'react';
import {Row, Col, Card, Tag, Typography, Modal, Form, Input, Select, Button, message, Empty, Space, Grid} from 'antd';
import {RocketOutlined, DollarOutlined, ShopOutlined, ApiOutlined, FolderOutlined, CheckCircleOutlined, PlusOutlined} from '@ant-design/icons';
import {resourceApi, projectApi} from '../api/api';
import GlassCard from './GlassCard';
import AnimatedButton from './AnimatedButton';
import {glacierTheme} from '../styles/theme';

const {Title, Text, Paragraph} = Typography;
const {TextArea} = Input;
const {Option} = Select;
const {useBreakpoint} = Grid;

const ResourceMarket = () => {
  const [resources, setResources] = useState([]);
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(false);
  const [applyModal, setApplyModal] = useState({open: false, resource: null});
  const [form] = Form.useForm();
  const screens = useBreakpoint();

  useEffect(() => {
    loadResources();
    loadProjects();
  }, []);

  const loadResources = async () => {
    try {
      setLoading(true);
      const res = await resourceApi.getPublicResources();
      setResources(res.data || []);
    } catch (e) {
      message.error('加载资源列表失败');
    } finally {
      setLoading(false);
    }
  };

  const loadProjects = async () => {
    try {
      const res = await projectApi.getAll();
      setProjects(res.data || []);
    } catch (e) {
      // 静默处理
    }
  };

  const handleApplyResource = async (values) => {
    try {
      await resourceApi.applyResource(applyModal.resource.resource_id, {
        project_id: values.project_id,
        message: values.message || '',
      });
      message.success('申请提交成功');
      setApplyModal({open: false, resource: null});
      form.resetFields();
      loadResources();
    } catch (e) {
      // 错误已在拦截器中处理
    }
  };

  const getResourceTypeIcon = (type) => {
    const iconMap = {
      '生产合同': <ShopOutlined/>,
      '技术支持': <RocketOutlined/>,
      '供应链服务': <ApiOutlined/>,
      '场地支持': <FolderOutlined/>,
      '资金支持': <DollarOutlined/>,
      '其他': <RocketOutlined/>,
    };
    return iconMap[type] || <RocketOutlined/>;
  };

  const getResourceTypeColor = (type) => {
    const colorMap = {
      '生产合同': glacierTheme.colors.primary,
      '技术支持': glacierTheme.colors.success,
      '供应链服务': glacierTheme.colors.info,
      '场地支持': glacierTheme.colors.warning,
      '资金支持': glacierTheme.colors.secondary,
      '其他': glacierTheme.colors.textSecondary,
    };
    return colorMap[type] || glacierTheme.colors.textSecondary;
  };

  // 筛选我的项目（只有状态为"孵化中"或"概念验证中"的项目可以申请）
  const availableProjects = projects.filter(p => 
    p.status === '孵化中' || p.status === '概念验证中'
  );

  return (
    <div style={{display: 'flex', flexDirection: 'column', gap: glacierTheme.spacing.xl}}>
      {/* 资源列表 */}
      {resources.length === 0 ? (
        <GlassCard>
          <Empty
            description="暂无开放中的资源"
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            style={{padding: glacierTheme.spacing.xl}}
          />
        </GlassCard>
      ) : (
        <Row gutter={[glacierTheme.spacing.lg, glacierTheme.spacing.lg]}>
          {resources.map((resource) => (
            <Col xs={24} sm={12} lg={8} key={resource.resource_id}>
              <GlassCard
                hoverable
                style={{
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                }}
              >
                <div style={{flex: 1}}>
                  <div style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'flex-start',
                    marginBottom: glacierTheme.spacing.md,
                  }}>
                    <Title level={4} style={{
                      margin: 0,
                      color: glacierTheme.colors.text,
                      fontWeight: 600,
                      flex: 1,
                    }}>
                      {resource.title}
                    </Title>
                  </div>

                  <Space direction="vertical" size="small" style={{width: '100%', marginBottom: glacierTheme.spacing.md}}>
                    <Tag
                      icon={getResourceTypeIcon(resource.resource_type)}
                      style={{
                        background: `${getResourceTypeColor(resource.resource_type)}20`,
                        border: `1px solid ${getResourceTypeColor(resource.resource_type)}`,
                        color: getResourceTypeColor(resource.resource_type),
                      }}
                    >
                      {resource.resource_type}
                    </Tag>
                    {resource.provider_name && (
                      <Text style={{
                        fontSize: '13px',
                        color: glacierTheme.colors.textSecondary,
                      }}>
                        发布者：{resource.provider_name}
                      </Text>
                    )}
                    {resource.provider_affiliation && (
                      <Text style={{
                        fontSize: '13px',
                        color: glacierTheme.colors.textSecondary,
                      }}>
                        所属单位：{resource.provider_affiliation}
                      </Text>
                    )}
                  </Space>

                  {resource.description && (
                    <Paragraph
                      ellipsis={{rows: 3, expandable: false}}
                      style={{
                        color: glacierTheme.colors.textSecondary,
                        fontSize: '14px',
                        marginBottom: glacierTheme.spacing.md,
                        minHeight: '60px',
                      }}
                    >
                      {resource.description}
                    </Paragraph>
                  )}
                </div>

                <div style={{marginTop: 'auto', paddingTop: glacierTheme.spacing.md}}>
                  <AnimatedButton
                    type="primary"
                    block
                    onClick={() => {
                      if (availableProjects.length === 0) {
                        message.warning('您没有可申请资源的项目（仅孵化中或概念验证中的项目可以申请）');
                        return;
                      }
                      setApplyModal({open: true, resource});
                      form.resetFields();
                    }}
                  >
                    申请对接
                  </AnimatedButton>
                </div>
              </GlassCard>
            </Col>
          ))}
        </Row>
      )}

      {/* 申请对接模态框 */}
      <Modal
        title={
          <span style={{fontSize: '18px', fontWeight: 600, color: glacierTheme.colors.text}}>
            申请资源对接
          </span>
        }
        open={applyModal.open}
        footer={null}
        onCancel={() => {
          setApplyModal({open: false, resource: null});
          form.resetFields();
        }}
        width={600}
        styles={{
          content: {
            background: glacierTheme.colors.background,
          },
        }}
      >
        {applyModal.resource && (
          <div style={{marginBottom: glacierTheme.spacing.lg}}>
            <div style={{marginBottom: glacierTheme.spacing.sm}}>
              <Text style={{color: glacierTheme.colors.textSecondary}}>资源标题：</Text>
              <Text strong style={{color: glacierTheme.colors.text, marginLeft: glacierTheme.spacing.xs}}>
                {applyModal.resource.title}
              </Text>
            </div>
            <div style={{marginBottom: glacierTheme.spacing.sm}}>
              <Text style={{color: glacierTheme.colors.textSecondary}}>资源类型：</Text>
              <Tag
                icon={getResourceTypeIcon(applyModal.resource.resource_type)}
                style={{
                  background: `${getResourceTypeColor(applyModal.resource.resource_type)}20`,
                  border: `1px solid ${getResourceTypeColor(applyModal.resource.resource_type)}`,
                  color: getResourceTypeColor(applyModal.resource.resource_type),
                  marginLeft: glacierTheme.spacing.xs,
                }}
              >
                {applyModal.resource.resource_type}
              </Tag>
            </div>
          </div>
        )}
        <Form
          form={form}
          layout="vertical"
          onFinish={handleApplyResource}
        >
          <Form.Item
            name="project_id"
            label="选择项目"
            rules={[{required: true, message: '请选择项目'}]}
          >
            <Select
              placeholder="请选择要关联的项目"
              style={{borderRadius: glacierTheme.borderRadius.md}}
            >
              {availableProjects.map(project => (
                <Option key={project.project_id} value={project.project_id}>
                  {project.project_name} ({project.status})
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="message"
            label="申请留言"
          >
            <TextArea
              rows={4}
              placeholder="请详细说明您的需求、合作意向等..."
              style={{borderRadius: glacierTheme.borderRadius.md}}
            />
          </Form.Item>

          <Form.Item style={{marginBottom: 0, marginTop: glacierTheme.spacing.lg}}>
            <Space style={{width: '100%', justifyContent: 'flex-end'}}>
              <Button
                onClick={() => {
                  setApplyModal({open: false, resource: null});
                  form.resetFields();
                }}
                style={{borderRadius: glacierTheme.borderRadius.md}}
              >
                取消
              </Button>
              <AnimatedButton type="primary" htmlType="submit">
                提交申请
              </AnimatedButton>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default ResourceMarket;
