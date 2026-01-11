import React, {useState, useEffect} from 'react';
import {List, Input, Button, Avatar, Typography, message, Space, Empty} from 'antd';
import {UserOutlined, SendOutlined, MessageOutlined} from '@ant-design/icons';
import {commentApi} from '../api/api';
import GlassCard from './GlassCard';
import AnimatedButton from './AnimatedButton';
import {glacierTheme} from '../styles/theme';

const {Text, Paragraph} = Typography;
const {TextArea} = Input;

const ReviewerGuidance = ({projectId}) => {
  const [comments, setComments] = useState([]);
  const [content, setContent] = useState('');
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (projectId) {
      loadComments();
    }
  }, [projectId]);

  const loadComments = async () => {
    try {
      setLoading(true);
      const res = await commentApi.getProjectComments(projectId);
      setComments(res.data || []);
    } catch (e) {
      message.error('加载留言失败');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async () => {
    if (!content.trim()) {
      message.warning('请输入留言内容');
      return;
    }

    try {
      setSubmitting(true);
      await commentApi.createComment(projectId, {content: content.trim()});
      message.success('留言发表成功');
      setContent('');
      loadComments();
    } catch (e) {
      // 错误已在拦截器中处理
    } finally {
      setSubmitting(false);
    }
  };

  const getRoleLabel = (role) => {
    const roleMap = {
      '评审人': '评审人',
      '项目参与者': '负责人',
      '管理员': '管理员',
      '秘书': '秘书',
    };
    return roleMap[role] || role;
  };

  const getRoleColor = (role) => {
    if (role === '评审人') return glacierTheme.colors.primary;
    if (role === '项目参与者') return glacierTheme.colors.secondary;
    return glacierTheme.colors.textSecondary;
  };

  return (
    <div>
      <List
        loading={loading}
        dataSource={comments}
        locale={{emptyText: <Empty description="暂无留言，快来发表第一条吧！" image={Empty.PRESENTED_IMAGE_SIMPLE}/>}}
        renderItem={(item) => (
          <List.Item style={{padding: 0, marginBottom: glacierTheme.spacing.md}}>
            <GlassCard
              style={{
                width: '100%',
                padding: glacierTheme.spacing.md,
              }}
            >
              <div style={{display: 'flex', gap: glacierTheme.spacing.md}}>
                <Avatar
                  icon={<UserOutlined/>}
                  style={{
                    background: getRoleColor(item.user_role),
                    flexShrink: 0,
                  }}
                />
                <div style={{flex: 1}}>
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: glacierTheme.spacing.xs,
                    marginBottom: glacierTheme.spacing.xs,
                  }}>
                    <Text strong style={{color: glacierTheme.colors.text}}>
                      {item.user_name}
                    </Text>
                    <Text style={{
                      fontSize: '12px',
                      color: getRoleColor(item.user_role),
                      padding: `2px ${glacierTheme.spacing.xs}`,
                      background: `${getRoleColor(item.user_role)}20`,
                      borderRadius: glacierTheme.borderRadius.sm,
                    }}>
                      [{getRoleLabel(item.user_role)}]
                    </Text>
                    {item.user_affiliation && (
                      <Text style={{
                        fontSize: '12px',
                        color: glacierTheme.colors.textLight,
                      }}>
                        {item.user_affiliation}
                      </Text>
                    )}
                  </div>
                  <Paragraph
                    style={{
                      margin: 0,
                      color: glacierTheme.colors.text,
                      whiteSpace: 'pre-wrap',
                    }}
                  >
                    {item.content}
                  </Paragraph>
                  <Text style={{
                    fontSize: '12px',
                    color: glacierTheme.colors.textLight,
                    marginTop: glacierTheme.spacing.xs,
                    display: 'block',
                  }}>
                    {new Date(item.create_time).toLocaleString('zh-CN')}
                  </Text>
                </div>
              </div>
            </GlassCard>
          </List.Item>
        )}
      />

      <GlassCard style={{marginTop: glacierTheme.spacing.lg}}>
        <div style={{marginBottom: glacierTheme.spacing.sm}}>
          <Text strong style={{color: glacierTheme.colors.text}}>
            <MessageOutlined style={{marginRight: glacierTheme.spacing.xs}}/>
            发表留言
          </Text>
        </div>
        <TextArea
          rows={4}
          value={content}
          onChange={(e) => setContent(e.target.value)}
          placeholder="请输入您的留言..."
          style={{
            borderRadius: glacierTheme.borderRadius.md,
            marginBottom: glacierTheme.spacing.md,
          }}
        />
        <div style={{display: 'flex', justifyContent: 'flex-end'}}>
          <AnimatedButton
            type="primary"
            icon={<SendOutlined/>}
            onClick={handleSubmit}
            loading={submitting}
          >
            发送
          </AnimatedButton>
        </div>
      </GlassCard>
    </div>
  );
};

export default ReviewerGuidance;
