import React, {useState, useEffect} from 'react';
import {List, Drawer, Form, Input, Select, DatePicker, Button, Empty, Tag, Typography, message, Space} from 'antd';
import {PlusOutlined, TrophyOutlined, CalendarOutlined, FileTextOutlined} from '@ant-design/icons';
import dayjs from 'dayjs';
import {achievementApi} from '../api/api';
import GlassCard from './GlassCard';
import AnimatedButton from './AnimatedButton';
import {glacierTheme} from '../styles/theme';

const {Text, Title} = Typography;
const {Option} = Select;
const {TextArea} = Input;

const AchievementList = ({projectId}) => {
  const [achievements, setAchievements] = useState([]);
  const [drawerVisible, setDrawerVisible] = useState(false);
  const [loading, setLoading] = useState(false);
  const [form] = Form.useForm();

  useEffect(() => {
    if (projectId) {
      loadAchievements();
    }
  }, [projectId]);

  const loadAchievements = async () => {
    try {
      setLoading(true);
      const res = await achievementApi.getProjectAchievements(projectId);
      setAchievements(res.data || []);
    } catch (e) {
      message.error('加载成果列表失败');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (values) => {
    try {
      await achievementApi.create({
        ...values,
        project_id: projectId,
        publish_time: values.publish_time ? values.publish_time.format('YYYY-MM-DD') : null,
      });
      message.success('成果录入成功');
      form.resetFields();
      setDrawerVisible(false);
      loadAchievements();
    } catch (e) {
      // 错误已在拦截器中处理
    }
  };

  const getTypeColor = (type) => {
    const typeMap = {
      '论文': glacierTheme.colors.primary,
      '专利': glacierTheme.colors.secondary,
      '软件著作权': glacierTheme.colors.success,
      '获奖': glacierTheme.colors.warning,
      '其他': glacierTheme.colors.info,
    };
    return typeMap[type] || glacierTheme.colors.textSecondary;
  };

  return (
    <div>
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: glacierTheme.spacing.md,
      }}>
        <Title level={5} style={{margin: 0, color: glacierTheme.colors.text}}>
          项目成果
        </Title>
        <AnimatedButton
          type="primary"
          icon={<PlusOutlined/>}
          onClick={() => setDrawerVisible(true)}
          size="small"
        >
          录入成果
        </AnimatedButton>
      </div>

      {achievements.length === 0 ? (
        <Empty
          description="暂无成果记录"
          image={Empty.PRESENTED_IMAGE_SIMPLE}
          style={{
            padding: glacierTheme.spacing.xl,
            color: glacierTheme.colors.textSecondary,
          }}
        />
      ) : (
        <List
          loading={loading}
          dataSource={achievements}
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
                      marginBottom: glacierTheme.spacing.xs,
                      gap: glacierTheme.spacing.sm,
                    }}>
                      <TrophyOutlined style={{
                        color: getTypeColor(item.type),
                        fontSize: '18px',
                      }}/>
                      <Text strong style={{
                        fontSize: '16px',
                        color: glacierTheme.colors.text,
                      }}>
                        {item.title}
                      </Text>
                      {item.type && (
                        <Tag style={{
                          background: `${getTypeColor(item.type)}20`,
                          border: `1px solid ${getTypeColor(item.type)}`,
                          color: getTypeColor(item.type),
                          marginLeft: glacierTheme.spacing.xs,
                        }}>
                          {item.type}
                        </Tag>
                      )}
                    </div>
                    {item.source_information && (
                      <div style={{
                        marginTop: glacierTheme.spacing.xs,
                        marginBottom: glacierTheme.spacing.xs,
                        color: glacierTheme.colors.textSecondary,
                        fontSize: '14px',
                      }}>
                        <FileTextOutlined style={{marginRight: glacierTheme.spacing.xs}}/>
                        {item.source_information}
                      </div>
                    )}
                    {item.publish_time && (
                      <div style={{
                        color: glacierTheme.colors.textLight,
                        fontSize: '12px',
                      }}>
                        <CalendarOutlined style={{marginRight: glacierTheme.spacing.xs}}/>
                        {new Date(item.publish_time).toLocaleDateString('zh-CN')}
                      </div>
                    )}
                  </div>
                </div>
              </GlassCard>
            </List.Item>
          )}
        />
      )}

      <Drawer
        title={
          <span style={{fontSize: '18px', fontWeight: 600, color: glacierTheme.colors.text}}>
            录入成果
          </span>
        }
        placement="right"
        width={480}
        onClose={() => {
          setDrawerVisible(false);
          form.resetFields();
        }}
        open={drawerVisible}
        styles={{
          body: {
            background: glacierTheme.colors.background,
          },
        }}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
        >
          <Form.Item
            name="title"
            label="成果标题"
            rules={[{required: true, message: '请输入成果标题'}]}
          >
            <Input
              placeholder="例如：基于深度学习的图像识别系统"
              style={{borderRadius: glacierTheme.borderRadius.md}}
            />
          </Form.Item>

          <Form.Item
            name="type"
            label="成果类型"
          >
            <Select
              placeholder="请选择成果类型"
              style={{borderRadius: glacierTheme.borderRadius.md}}
            >
              <Option value="论文">论文</Option>
              <Option value="专利">专利</Option>
              <Option value="软件著作权">软件著作权</Option>
              <Option value="获奖">获奖</Option>
              <Option value="其他">其他</Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="publish_time"
            label="发布时间"
          >
            <DatePicker
              style={{width: '100%', borderRadius: glacierTheme.borderRadius.md}}
              format="YYYY-MM-DD"
              placeholder="选择发布日期"
            />
          </Form.Item>

          <Form.Item
            name="source_information"
            label="来源信息"
          >
            <TextArea
              rows={4}
              placeholder="例如：期刊名称、会议名称、专利号等"
              style={{borderRadius: glacierTheme.borderRadius.md}}
            />
          </Form.Item>

          <Form.Item style={{marginBottom: 0, marginTop: glacierTheme.spacing.lg}}>
            <Space style={{width: '100%', justifyContent: 'flex-end'}}>
              <Button
                onClick={() => {
                  setDrawerVisible(false);
                  form.resetFields();
                }}
                style={{borderRadius: glacierTheme.borderRadius.md}}
              >
                取消
              </Button>
              <AnimatedButton type="primary" htmlType="submit">
                提交
              </AnimatedButton>
            </Space>
          </Form.Item>
        </Form>
      </Drawer>
    </div>
  );
};

export default AchievementList;
