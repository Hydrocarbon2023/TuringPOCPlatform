import {LockOutlined, UserOutlined} from '@ant-design/icons';
import {App as AntdApp, Button, Card, Form, Input, message, Typography} from 'antd';
import React, {useState} from 'react';
import {Link, useNavigate} from 'react-router-dom';

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
      message.success(`欢迎回来，${res.data.user_name}$`);
      navigate('/dashboard');
    } catch (err) {
      console.error(err);
      message.error(err.response?.data?.message || '登录失败，请重试TT');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      height: '100vh',
      background: 'linear-gradient(135deg, #F5F7FA 0%, #E74C3C 100%)'
    }}>
      <Card style={{width: 400, boxShadow: '0 0px 24px rgba(0,0,0,0.1)'}}
            variant="borderless"
      >
        <div style={{textAlign: 'center', marginBottom: 32}}>
          <Title level={3} style={{color: '#4A6C92'}}>登录</Title>
          <Text type="secondary">图灵数智概念验证平台</Text>
        </div>

        <Form onFinish={onFinish} layout="vertical" size="large">
          <Form.Item name="user_name" rules={[{required: true, message: '请输入用户名'}]}>
            <Input prefix={<UserOutlined/>} placeholder="用户名"/>
          </Form.Item>
          <Form.Item name="password" rules={[{required: true, message: '请输入密码'}]}>
            <Input.Password prefix={<LockOutlined/>} placeholder="密码"/>
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading} block shape="round">
              登录
            </Button>
          </Form.Item>
          <div style={{textAlign: 'center'}}>
            <Text type="secondary">还没有账号？<Link to="/register">点击注册</Link></Text>
          </div>
        </Form>
      </Card>
    </div>
  );
};

export default Login;
