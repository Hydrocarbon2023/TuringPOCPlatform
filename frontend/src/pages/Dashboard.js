import React, { useEffect, useState } from 'react';
import { Layout, Spin, Result, Button } from 'antd';
import { useNavigate } from 'react-router-dom';
import UserDashboard from './user/UserDashboard';
import ExpertDashboard from './expert/ExpertDashboard';
import AdminDashboard from './admin/AdminDashboard';
import SecretaryDashboard from './secretary/SecretaryDashboard';

const { Content } = Layout;

const Dashboard = () => {
  const [role, setRole] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    const storedRole = localStorage.getItem('role');
    const token = localStorage.getItem('token');
    if (!token || !storedRole) {
      navigate('/login');
    } else {
      setRole(storedRole);
    }
  }, [navigate]);

  if (!role) {
    return <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />;
  }

  const renderDashboard = () => {
    switch (role) {
      case '项目参与者': return <UserDashboard />;
      case '评审人': return <ExpertDashboard />;
      case '管理员': return <AdminDashboard />;
      case '秘书': return <SecretaryDashboard />;
      default:
        return <Result status="403" title="权限错误" extra={<Button onClick={() => navigate('/login')}>返回登录</Button>} />;
    }
  };

  return <Layout style={{ padding: '24px 0', background: '#fff' }}><Content>{renderDashboard()}</Content></Layout>;
};

export default Dashboard;
