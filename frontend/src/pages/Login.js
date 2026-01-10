import {LockOutlined, UserOutlined} from '@ant-design/icons';
import {App as AntdApp, Button, Form, Input, Typography} from 'antd';
import React, {useState} from 'react';
import {Link, useNavigate} from 'react-router-dom';
import GlassCard from '../components/GlassCard';
import AnimatedButton from '../components/AnimatedButton';
import {glacierTheme} from '../styles/theme';
import api from '../api/api';

const {Text, Title} = Typography;

const Login = () => {
  const {message} = AntdApp.useApp();
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const onFinish = async (values) => {
    setLoading(true);
    try {
      const res = await api.post('/login', values);
      localStorage.setItem('token', res.data.token);
      localStorage.setItem('role', res.data.role);
      localStorage.setItem('user_name', res.data.user_name);
      message.success(`欢迎回来，${res.data.user_name}`);
      navigate('/dashboard');
    } catch (err) {
      console.error(err);
      message.error(err.response?.data?.message || '登录失败，请重试');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      minHeight: '100vh',
      background: `linear-gradient(135deg, ${glacierTheme.colors.background} 0%, ${glacierTheme.colors.surface} 50%, ${glacierTheme.colors.primaryLight} 70%, ${glacierTheme.colors.secondaryLight} 100%)`,
      position: 'relative',
      padding: glacierTheme.spacing.lg,
    }}>
      {/* 背景装饰 */}
      <div style={{
        position: 'absolute',
        width: '400px',
        height: '400px',
        borderRadius: '50%',
        background: `radial-gradient(circle, ${glacierTheme.colors.primaryLight}30 0%, transparent 70%)`,
        top: '-100px',
        right: '-100px',
        filter: 'blur(60px)',
      }}/>
      <div style={{
        position: 'absolute',
        width: '300px',
        height: '300px',
        borderRadius: '50%',
        background: `radial-gradient(circle, ${glacierTheme.colors.secondaryLight}30 0%, transparent 70%)`,
        bottom: '-50px',
        left: '-50px',
        filter: 'blur(60px)',
      }}/>

      <GlassCard
        style={{
          width: '100%',
          maxWidth: 420,
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
            登录
          </Title>
          <Text style={{color: glacierTheme.colors.textSecondary, fontSize: '14px'}}>
            图灵数智概念验证平台
          </Text>
        </div>

        <Form onFinish={onFinish} layout="vertical" size="large">
          <Form.Item name="user_name" rules={[{required: true, message: '请输入用户名'}]}>
            <Input
              prefix={<UserOutlined style={{color: glacierTheme.colors.primary}}/>}
              placeholder="用户名"
              style={{
                borderRadius: glacierTheme.borderRadius.md,
                border: `1px solid ${glacierTheme.colors.border}`,
              }}
            />
          </Form.Item>
          <Form.Item name="password" rules={[{required: true, message: '请输入密码'}]}>
            <Input.Password
              prefix={<LockOutlined style={{color: glacierTheme.colors.primary}}/>}
              placeholder="密码"
              style={{
                borderRadius: glacierTheme.borderRadius.md,
                border: `1px solid ${glacierTheme.colors.border}`,
              }}
            />
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
              登录
            </AnimatedButton>
          </Form.Item>
          <div style={{textAlign: 'center', marginTop: glacierTheme.spacing.md}}>
            <Text style={{color: glacierTheme.colors.textSecondary}}>
              还没有账号？<Link to="/register" style={{
              color: glacierTheme.colors.primary,
              fontWeight: 500,
              textDecoration: 'none',
            }}>点击注册</Link>
            </Text>
          </div>
        </Form>
      </GlassCard>
    </div>
  );
};

export default Login;
