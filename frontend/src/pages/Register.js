import {Button, Form, Input, Select, message, Typography} from 'antd';

const {Option} = Select;
import React, {useState} from 'react';
import {Link, useNavigate} from 'react-router-dom';
import GlassCard from '../components/GlassCard';
import AnimatedButton from '../components/AnimatedButton';
import {glacierTheme} from '../styles/theme';
import api from '../api/api';

const {Text, Title} = Typography;

const Register = () => {
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const onFinish = async (values) => {
    setLoading(true);
    try {
      await api.post('/register', values);
      message.success('注册成功！');
      navigate('/login');
    } catch (err) {
      message.error('注册失败，请重试');
    }
    setLoading(false);
  };

  return (
    <div style={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      minHeight: '100vh',
      background: `linear-gradient(135deg, ${glacierTheme.colors.background} 0%, ${glacierTheme.colors.surface} 50%, ${glacierTheme.colors.secondaryLight} 70%, ${glacierTheme.colors.primaryLight} 100%)`,
      position: 'relative',
      padding: glacierTheme.spacing.lg,
    }}>
      {/* 背景装饰 */}
      <div style={{
        position: 'absolute',
        width: '400px',
        height: '400px',
        borderRadius: '50%',
        background: `radial-gradient(circle, ${glacierTheme.colors.secondaryLight}30 0%, transparent 70%)`,
        top: '-100px',
        left: '-100px',
        filter: 'blur(60px)',
      }}/>

      <GlassCard
        style={{
          width: '100%',
          maxWidth: 480,
          position: 'relative',
          zIndex: 1,
        }}
        hoverable
      >
        <div style={{textAlign: 'center', marginBottom: glacierTheme.spacing.xl}}>
          <Title level={2} style={{
            margin: 0,
            marginBottom: glacierTheme.spacing.sm,
            background: `linear-gradient(135deg, ${glacierTheme.colors.primary} 0%, ${glacierTheme.colors.secondary} 100%)`,
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            backgroundClip: 'text',
            fontWeight: 600,
          }}>
            注册账号
          </Title>
          <Text style={{color: glacierTheme.colors.textSecondary, fontSize: '14px'}}>
            创建您的账户
          </Text>
        </div>

        <Form onFinish={onFinish} layout="vertical" size="large">
          <Form.Item name='user_name' rules={[{required: true, message: '请输入用户名'}]}>
            <Input
              placeholder='用户名'
              style={{
                borderRadius: glacierTheme.borderRadius.md,
                border: `1px solid ${glacierTheme.colors.border}`,
              }}
            />
          </Form.Item>
          <Form.Item name='password' rules={[{required: true, message: '请输入密码'}]}>
            <Input.Password
              placeholder='密码'
              style={{
                borderRadius: glacierTheme.borderRadius.md,
                border: `1px solid ${glacierTheme.colors.border}`,
              }}
            />
          </Form.Item>
          <Form.Item name='real_name'>
            <Input
              placeholder='真实姓名'
              style={{
                borderRadius: glacierTheme.borderRadius.md,
                border: `1px solid ${glacierTheme.colors.border}`,
              }}
            />
          </Form.Item>
          <Form.Item name='affiliation'>
            <Input
              placeholder='所属单位'
              style={{
                borderRadius: glacierTheme.borderRadius.md,
                border: `1px solid ${glacierTheme.colors.border}`,
              }}
            />
          </Form.Item>
          <Form.Item name='email'>
            <Input
              placeholder='邮箱'
              style={{
                borderRadius: glacierTheme.borderRadius.md,
                border: `1px solid ${glacierTheme.colors.border}`,
              }}
            />
          </Form.Item>
          <Form.Item name='role' label="注册类型" initialValue="项目参与者">
            <Select
              placeholder='选择注册类型'
              style={{
                borderRadius: glacierTheme.borderRadius.md,
                border: `1px solid ${glacierTheme.colors.border}`,
              }}
            >
              <Option value="项目参与者">项目参与者</Option>
              <Option value="评审人">评审人</Option>
              <Option value="秘书">秘书</Option>
              <Option value="企业支持者">企业支持者</Option>
            </Select>
          </Form.Item>
          <Form.Item>
            <AnimatedButton
              type="primary"
              htmlType="submit"
              loading={loading}
              block
              style={{
                height: '44px',
                fontSize: '16px',
                fontWeight: 500,
              }}
            >
              注册
            </AnimatedButton>
          </Form.Item>
          <div style={{textAlign: 'center', marginTop: glacierTheme.spacing.md}}>
            <Text style={{color: glacierTheme.colors.textSecondary}}>
              已有账号？<Link to="/login" style={{
              color: glacierTheme.colors.primary,
              fontWeight: 500,
              textDecoration: 'none',
            }}>立即登录</Link>
            </Text>
          </div>
        </Form>
      </GlassCard>
    </div>
  );
};

export default Register;
