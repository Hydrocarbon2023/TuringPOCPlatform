import React, {useState, useEffect} from 'react';
import {Row, Col, Card, Tag, Typography, Modal, Form, Input, Select, Button, message, Empty, Space, Tabs, Table, Drawer} from 'antd';
import {RocketOutlined, DollarOutlined, ShopOutlined, ApiOutlined, CheckCircleOutlined, CloseCircleOutlined, ClockCircleOutlined, FolderOutlined, PlusOutlined, EyeOutlined} from '@ant-design/icons';
import {supporterApi} from '../../api/api';
import GlassCard from '../../components/GlassCard';
import AnimatedButton from '../../components/AnimatedButton';
import {glacierTheme} from '../../styles/theme';

const {Title, Text, Paragraph} = Typography;
const {TextArea} = Input;
const {Option} = Select;

const SupporterDashboard = () => {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(false);
  const [intentionModal, setIntentionModal] = useState({open: false, project: null});
  const [form] = Form.useForm();
  
  // 资源管理相关状态
  const [resources, setResources] = useState([]);
  const [resourcesLoading, setResourcesLoading] = useState(false);
  const [resourceModal, setResourceModal] = useState({open: false, resource: null});
  const [applicationsDrawer, setApplicationsDrawer] = useState({open: false, resource: null});
  const [applications, setApplications] = useState([]);
  const [applicationHandleModal, setApplicationHandleModal] = useState({open: false, application: null});
  const [resourceForm] = Form.useForm();
  const [applicationHandleForm] = Form.useForm();

  useEffect(() => {
    loadProjects();
    loadResources();
  }, []);

  const loadProjects = async () => {
    try {
      setLoading(true);
      const res = await supporterApi.getProjects();
      setProjects(res.data || []);
    } catch (e) {
      message.error('加载项目列表失败');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitIntention = async (values) => {
    try {
      await supporterApi.submitIntention({
        project_id: intentionModal.project.project_id,
        support_type: values.support_type,
        message: values.message || '',
      });
      message.success('对接意向提交成功');
      setIntentionModal({open: false, project: null});
      form.resetFields();
      loadProjects();
    } catch (e) {
      // 错误已在拦截器中处理
    }
  };

  const getMaturityLevelColor = (level) => {
    const levelMap = {
      '研发阶段': glacierTheme.colors.info,
      '小试阶段': glacierTheme.colors.primary,
      '中试阶段': glacierTheme.colors.warning,
      '小批量生产阶段': glacierTheme.colors.success,
    };
    return levelMap[level] || glacierTheme.colors.textSecondary;
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

  // 资源管理相关函数
  const loadResources = async () => {
    try {
      setResourcesLoading(true);
      const res = await supporterApi.getMyResources();
      setResources(res.data || []);
    } catch (e) {
      message.error('加载资源列表失败');
    } finally {
      setResourcesLoading(false);
    }
  };

  const handleCreateResource = async (values) => {
    try {
      await supporterApi.createResource(values);
      message.success('资源发布成功');
      setResourceModal({open: false, resource: null});
      resourceForm.resetFields();
      loadResources();
    } catch (e) {
      // 错误已在拦截器中处理
    }
  };

  const handleViewApplications = async (resource) => {
    try {
      setApplicationsDrawer({open: true, resource});
      const res = await supporterApi.getResourceApplications(resource.resource_id);
      setApplications(res.data || []);
    } catch (e) {
      message.error('加载申请列表失败');
    }
  };

  const handleApplicationHandle = async (values) => {
    try {
      await supporterApi.handleApplication(applicationHandleModal.application.application_id, values);
      message.success('申请处理成功');
      setApplicationHandleModal({open: false, application: null});
      applicationHandleForm.resetFields();
      if (applicationsDrawer.resource) {
        handleViewApplications(applicationsDrawer.resource);
      }
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

  const getStatusColor = (status) => {
    switch (status) {
      case '对接中':
        return glacierTheme.colors.primary;
      case '已达成':
        return glacierTheme.colors.success;
      case '已拒绝':
        return glacierTheme.colors.error;
      default:
        return glacierTheme.colors.warning;
    }
  };

  const resourceColumns = [
    {
      title: '资源标题',
      dataIndex: 'title',
      key: 'title',
      render: (text) => <Text strong style={{color: glacierTheme.colors.text}}>{text}</Text>,
    },
    {
      title: '资源类型',
      dataIndex: 'resource_type',
      key: 'resource_type',
      render: (type) => (
        <Tag
          icon={getResourceTypeIcon(type)}
          style={{
            background: `${glacierTheme.colors.primary}20`,
            border: `1px solid ${glacierTheme.colors.primary}`,
            color: glacierTheme.colors.primary,
          }}
        >
          {type}
        </Tag>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status) => (
        <Tag
          style={{
            background: status === '开放中' ? `${glacierTheme.colors.success}20` : `${glacierTheme.colors.textSecondary}20`,
            border: `1px solid ${status === '开放中' ? glacierTheme.colors.success : glacierTheme.colors.textSecondary}`,
            color: status === '开放中' ? glacierTheme.colors.success : glacierTheme.colors.textSecondary,
          }}
        >
          {status}
        </Tag>
      ),
    },
    {
      title: '发布时间',
      dataIndex: 'create_time',
      key: 'create_time',
      render: (time) => <Text style={{color: glacierTheme.colors.textSecondary}}>{new Date(time).toLocaleDateString('zh-CN')}</Text>,
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Space>
          <Button
            type="link"
            icon={<EyeOutlined/>}
            onClick={() => handleViewApplications(record)}
            style={{color: glacierTheme.colors.primary}}
          >
            查看申请
          </Button>
        </Space>
      ),
    },
  ];

  const applicationColumns = [
    {
      title: '项目名称',
      dataIndex: 'project_name',
      key: 'project_name',
      render: (text) => <Text strong style={{color: glacierTheme.colors.text}}>{text}</Text>,
    },
    {
      title: '申请人',
      dataIndex: 'applicant_name',
      key: 'applicant_name',
      render: (text, record) => (
        <div>
          <Text style={{color: glacierTheme.colors.text}}>{text}</Text>
          {record.applicant_affiliation && (
            <Text style={{color: glacierTheme.colors.textSecondary, fontSize: '12px', marginLeft: glacierTheme.spacing.xs}}>
              ({record.applicant_affiliation})
            </Text>
          )}
        </div>
      ),
    },
    {
      title: '申请状态',
      dataIndex: 'status',
      key: 'status',
      render: (status) => (
        <Tag
          style={{
            background: `${getStatusColor(status)}20`,
            border: `1px solid ${getStatusColor(status)}`,
            color: getStatusColor(status),
          }}
        >
          {status}
        </Tag>
      ),
    },
    {
      title: '申请时间',
      dataIndex: 'create_time',
      key: 'create_time',
      render: (time) => <Text style={{color: glacierTheme.colors.textSecondary}}>{new Date(time).toLocaleDateString('zh-CN')}</Text>,
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        record.status === '待处理' && (
          <Space>
            <Button
              type="link"
              size="small"
              onClick={() => {
                applicationHandleForm.setFieldsValue({status: record.status, reply: record.reply || ''});
                setApplicationHandleModal({open: true, application: record});
              }}
              style={{color: glacierTheme.colors.primary}}
            >
              处理
            </Button>
          </Space>
        )
      ),
    },
  ];

  return (
    <div style={{display: 'flex', flexDirection: 'column', gap: glacierTheme.spacing.xl}}>
      {/* 标题区域 */}
      <GlassCard>
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}>
          <div>
            <Title level={2} style={{margin: 0, color: glacierTheme.colors.text, fontWeight: 600}}>
              企业支持者看板
            </Title>
            <Text style={{
              color: glacierTheme.colors.textSecondary,
              fontSize: '14px',
              marginTop: glacierTheme.spacing.xs,
              display: 'block',
            }}>
              浏览孵化项目，发布资源，促进产学研融合
            </Text>
          </div>
        </div>
      </GlassCard>

      {/* 使用Tabs组织内容 */}
      <GlassCard>
        <Tabs
          items={[
            {
              key: '1',
              label: '孵化项目',
              children: (
                <div>
                  {/* 项目卡片墙 */}
      {projects.length === 0 ? (
        <GlassCard>
          <Empty
            description="暂无孵化中的项目"
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            style={{padding: glacierTheme.spacing.xl}}
          />
        </GlassCard>
      ) : (
        <Row gutter={[glacierTheme.spacing.lg, glacierTheme.spacing.lg]}>
          {projects.map((project) => (
            <Col xs={24} sm={12} lg={8} key={project.project_id}>
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
                      {project.project_name}
                    </Title>
                  </div>

                  <Space direction="vertical" size="small" style={{width: '100%', marginBottom: glacierTheme.spacing.md}}>
                    <div>
                      <Tag style={{
                        background: `${glacierTheme.colors.primary}20`,
                        border: `1px solid ${glacierTheme.colors.primary}`,
                        color: glacierTheme.colors.primary,
                      }}>
                        {project.status}
                      </Tag>
                      <Tag style={{
                        background: `${getMaturityLevelColor(project.maturity_level)}20`,
                        border: `1px solid ${getMaturityLevelColor(project.maturity_level)}`,
                        color: getMaturityLevelColor(project.maturity_level),
                        marginLeft: glacierTheme.spacing.xs,
                      }}>
                        {project.maturity_level}
                      </Tag>
                    </div>
                    {project.domain && (
                      <Text style={{
                        fontSize: '13px',
                        color: glacierTheme.colors.textSecondary,
                      }}>
                        领域：{project.domain}
                      </Text>
                    )}
                    {project.principal_name && (
                      <Text style={{
                        fontSize: '13px',
                        color: glacierTheme.colors.textSecondary,
                      }}>
                        负责人：{project.principal_name}
                      </Text>
                    )}
                  </Space>

                  {project.project_description && (
                    <Paragraph
                      ellipsis={{rows: 3, expandable: false}}
                      style={{
                        color: glacierTheme.colors.textSecondary,
                        fontSize: '14px',
                        marginBottom: glacierTheme.spacing.md,
                        minHeight: '60px',
                      }}
                    >
                      {project.project_description}
                    </Paragraph>
                  )}
                </div>

                <div style={{marginTop: 'auto', paddingTop: glacierTheme.spacing.md}}>
                  <AnimatedButton
                    type="primary"
                    block
                    onClick={() => {
                      setIntentionModal({open: true, project});
                      form.resetFields();
                    }}
                  >
                    建立连接
                  </AnimatedButton>
                </div>
              </GlassCard>
            </Col>
          ))}
        </Row>
      )}
                </div>
              ),
            },
            {
              key: '2',
              label: '资源管理',
              icon: <FolderOutlined/>,
              children: (
                <div>
                  <div style={{display: 'flex', justifyContent: 'flex-end', marginBottom: glacierTheme.spacing.md}}>
                    <AnimatedButton
                      type="primary"
                      icon={<PlusOutlined/>}
                      onClick={() => {
                        setResourceModal({open: true, resource: null});
                        resourceForm.resetFields();
                      }}
                    >
                      发布资源
                    </AnimatedButton>
                  </div>
                  <Table
                    columns={resourceColumns}
                    dataSource={resources}
                    loading={resourcesLoading}
                    rowKey="resource_id"
                    locale={{emptyText: <Empty description="暂无发布的资源"/>}}
                  />
                </div>
              ),
            },
          ]}
        />
      </GlassCard>

      {/* 对接意向模态框 */}
      <Modal
        title={
          <span style={{fontSize: '18px', fontWeight: 600, color: glacierTheme.colors.text}}>
            提交对接意向
          </span>
        }
        open={intentionModal.open}
        footer={null}
        onCancel={() => {
          setIntentionModal({open: false, project: null});
          form.resetFields();
        }}
        width={600}
        styles={{
          content: {
            background: glacierTheme.colors.background,
          },
        }}
      >
        {intentionModal.project && (
          <div style={{marginBottom: glacierTheme.spacing.lg}}>
            <Text style={{color: glacierTheme.colors.textSecondary}}>项目名称：</Text>
            <Text strong style={{color: glacierTheme.colors.text, marginLeft: glacierTheme.spacing.xs}}>
              {intentionModal.project.project_name}
            </Text>
          </div>
        )}
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmitIntention}
        >
          <Form.Item
            name="support_type"
            label="支持类型"
            rules={[{required: true, message: '请选择支持类型'}]}
          >
            <Select
              placeholder="请选择您能提供的支持类型"
              style={{borderRadius: glacierTheme.borderRadius.md}}
            >
              <Option value="资金支持">
                <Space>
                  <DollarOutlined/>
                  资金支持
                </Space>
              </Option>
              <Option value="产业资源">
                <Space>
                  <ShopOutlined/>
                  产业资源
                </Space>
              </Option>
              <Option value="市场渠道">
                <Space>
                  <ApiOutlined/>
                  市场渠道
                </Space>
              </Option>
              <Option value="其他">
                <Space>
                  <RocketOutlined/>
                  其他
                </Space>
              </Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="message"
            label="留言说明"
          >
            <TextArea
              rows={4}
              placeholder="请详细说明您能提供的支持内容、合作方式等..."
              style={{borderRadius: glacierTheme.borderRadius.md}}
            />
          </Form.Item>

          <Form.Item style={{marginBottom: 0, marginTop: glacierTheme.spacing.lg}}>
            <Space style={{width: '100%', justifyContent: 'flex-end'}}>
              <Button
                onClick={() => {
                  setIntentionModal({open: false, project: null});
                  form.resetFields();
                }}
                style={{borderRadius: glacierTheme.borderRadius.md}}
              >
                取消
              </Button>
              <AnimatedButton type="primary" htmlType="submit">
                提交意向
              </AnimatedButton>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 发布资源模态框 */}
      <Modal
        title={
          <span style={{fontSize: '18px', fontWeight: 600, color: glacierTheme.colors.text}}>
            {resourceModal.resource ? '编辑资源' : '发布资源'}
          </span>
        }
        open={resourceModal.open}
        footer={null}
        onCancel={() => {
          setResourceModal({open: false, resource: null});
          resourceForm.resetFields();
        }}
        width={600}
        styles={{
          content: {
            background: glacierTheme.colors.background,
          },
        }}
      >
        <Form
          form={resourceForm}
          layout="vertical"
          onFinish={handleCreateResource}
        >
          <Form.Item
            name="title"
            label="资源标题"
            rules={[{required: true, message: '请输入资源标题'}]}
          >
            <Input
              placeholder="例如：提供生产线代工服务"
              style={{borderRadius: glacierTheme.borderRadius.md}}
            />
          </Form.Item>

          <Form.Item
            name="resource_type"
            label="资源类型"
            rules={[{required: true, message: '请选择资源类型'}]}
          >
            <Select
              placeholder="请选择资源类型"
              style={{borderRadius: glacierTheme.borderRadius.md}}
            >
              <Option value="生产合同">
                <Space>
                  <ShopOutlined/>
                  生产合同
                </Space>
              </Option>
              <Option value="技术支持">
                <Space>
                  <RocketOutlined/>
                  技术支持
                </Space>
              </Option>
              <Option value="供应链服务">
                <Space>
                  <ApiOutlined/>
                  供应链服务
                </Space>
              </Option>
              <Option value="场地支持">
                <Space>
                  <FolderOutlined/>
                  场地支持
                </Space>
              </Option>
              <Option value="资金支持">
                <Space>
                  <DollarOutlined/>
                  资金支持
                </Space>
              </Option>
              <Option value="其他">
                <Space>
                  <RocketOutlined/>
                  其他
                </Space>
              </Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="description"
            label="详细描述"
          >
            <TextArea
              rows={6}
              placeholder="请详细描述您能提供的资源、服务内容、合作方式等..."
              style={{borderRadius: glacierTheme.borderRadius.md}}
            />
          </Form.Item>

          <Form.Item style={{marginBottom: 0, marginTop: glacierTheme.spacing.lg}}>
            <Space style={{width: '100%', justifyContent: 'flex-end'}}>
              <Button
                onClick={() => {
                  setResourceModal({open: false, resource: null});
                  resourceForm.resetFields();
                }}
                style={{borderRadius: glacierTheme.borderRadius.md}}
              >
                取消
              </Button>
              <AnimatedButton type="primary" htmlType="submit">
                发布
              </AnimatedButton>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 查看申请抽屉 */}
      <Drawer
        title={
          <span style={{fontSize: '18px', fontWeight: 600, color: glacierTheme.colors.text}}>
            资源申请列表：{applicationsDrawer.resource?.title}
          </span>
        }
        width={800}
        open={applicationsDrawer.open}
        onClose={() => setApplicationsDrawer({open: false, resource: null})}
        styles={{
          body: {
            background: glacierTheme.colors.background,
          },
        }}
      >
        <Table
          columns={applicationColumns}
          dataSource={applications}
          rowKey="application_id"
          locale={{emptyText: <Empty description="暂无申请"/>}}
          expandable={{
            expandedRowRender: (record) => (
              <div style={{padding: glacierTheme.spacing.md, background: glacierTheme.colors.surface, borderRadius: glacierTheme.borderRadius.md}}>
                {record.message && (
                  <div style={{marginBottom: glacierTheme.spacing.md}}>
                    <Text strong style={{color: glacierTheme.colors.text}}>申请留言：</Text>
                    <Paragraph style={{marginTop: glacierTheme.spacing.xs, marginBottom: 0}}>
                      {record.message}
                    </Paragraph>
                  </div>
                )}
                {record.reply && (
                  <div>
                    <Text strong style={{color: glacierTheme.colors.text}}>企业回复：</Text>
                    <Paragraph style={{marginTop: glacierTheme.spacing.xs, marginBottom: 0}}>
                      {record.reply}
                    </Paragraph>
                  </div>
                )}
              </div>
            ),
          }}
        />
      </Drawer>

      {/* 处理申请模态框 */}
      <Modal
        title={
          <span style={{fontSize: '18px', fontWeight: 600, color: glacierTheme.colors.text}}>
            处理申请
          </span>
        }
        open={applicationHandleModal.open}
        footer={null}
        onCancel={() => {
          setApplicationHandleModal({open: false, application: null});
          applicationHandleForm.resetFields();
        }}
        width={600}
        styles={{
          content: {
            background: glacierTheme.colors.background,
          },
        }}
      >
        {applicationHandleModal.application && (
          <div style={{marginBottom: glacierTheme.spacing.lg}}>
            <div style={{marginBottom: glacierTheme.spacing.sm}}>
              <Text style={{color: glacierTheme.colors.textSecondary}}>项目名称：</Text>
              <Text strong style={{color: glacierTheme.colors.text, marginLeft: glacierTheme.spacing.xs}}>
                {applicationHandleModal.application.project_name}
              </Text>
            </div>
            {applicationHandleModal.application.message && (
              <div style={{
                padding: glacierTheme.spacing.md,
                background: glacierTheme.colors.surface,
                borderRadius: glacierTheme.borderRadius.md,
                marginBottom: glacierTheme.spacing.md,
              }}>
                <Text style={{color: glacierTheme.colors.textSecondary}}>申请留言：</Text>
                <Paragraph style={{marginTop: glacierTheme.spacing.xs, marginBottom: 0}}>
                  {applicationHandleModal.application.message}
                </Paragraph>
              </div>
            )}
          </div>
        )}
        <Form
          form={applicationHandleForm}
          layout="vertical"
          onFinish={handleApplicationHandle}
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
              <Option value="对接中">对接中</Option>
              <Option value="已达成">已达成</Option>
              <Option value="已拒绝">已拒绝</Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="reply"
            label="回复内容"
          >
            <TextArea
              rows={4}
              placeholder="请输入回复内容..."
              style={{borderRadius: glacierTheme.borderRadius.md}}
            />
          </Form.Item>

          <Form.Item style={{marginBottom: 0, marginTop: glacierTheme.spacing.lg}}>
            <Space style={{width: '100%', justifyContent: 'flex-end'}}>
              <Button
                onClick={() => {
                  setApplicationHandleModal({open: false, application: null});
                  applicationHandleForm.resetFields();
                }}
                style={{borderRadius: glacierTheme.borderRadius.md}}
              >
                取消
              </Button>
              <AnimatedButton type="primary" htmlType="submit">
                确认
              </AnimatedButton>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default SupporterDashboard;
