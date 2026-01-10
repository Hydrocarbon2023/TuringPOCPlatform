import {LogoutOutlined, UserOutlined} from '@ant-design/icons';
import {Avatar, Dropdown, Layout, Space, theme} from 'antd';
import React from 'react';
import {useNavigate} from 'react-router-dom';
import {glacierTheme} from '../styles/theme';

const {Header} = Layout;

const AppHeader = () => {
  const navigate = useNavigate();
  const {token} = theme.useToken();
  const role = localStorage.getItem('role');
  const username = localStorage.getItem('username') || '用户';

  const handleLogout = () => {
    localStorage.clear();
    navigate('/login');
  };

  const items = [
    {
      key: '1',
      label: <span onClick={handleLogout}><LogoutOutlined/>退出登录</span>,
    },
  ];

  return (
    <Header style={{
      background: glacierTheme.glass.background,
      backdropFilter: glacierTheme.glass.backdropFilter,
      borderBottom: glacierTheme.glass.border,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      boxShadow: glacierTheme.shadows.glass,
      padding: `0 ${glacierTheme.spacing.lg}`,
      position: 'sticky',
      top: 0,
      zIndex: 100,
      transition: `all ${glacierTheme.transitions.normal}`,
    }}>
      <div style={{
        fontSize: '20px',
        fontWeight: 600,
        background: `linear-gradient(135deg, ${glacierTheme.colors.primary} 0%, ${glacierTheme.colors.secondary} 100%)`,
        WebkitBackgroundClip: 'text',
        WebkitTextFillColor: 'transparent',
        backgroundClip: 'text',
      }}>
        🚀 图灵数智概念验证平台
      </div>
      <Space>
        <span style={{
          color: glacierTheme.colors.textSecondary,
          padding: `${glacierTheme.spacing.xs} ${glacierTheme.spacing.md}`,
          borderRadius: glacierTheme.borderRadius.md,
          background: glacierTheme.colors.surface,
          fontSize: '13px',
        }}>{role}</span>
        <Dropdown menu={{items}} placement="bottomRight">
          <Space style={{
            cursor: 'pointer',
            padding: `${glacierTheme.spacing.xs} ${glacierTheme.spacing.md}`,
            borderRadius: glacierTheme.borderRadius.md,
            transition: `all ${glacierTheme.transitions.fast}`,
          }}
                 onMouseEnter={(e) => {
                   e.currentTarget.style.background = glacierTheme.colors.surfaceHover;
                 }}
                 onMouseLeave={(e) => {
                   e.currentTarget.style.background = 'transparent';
                 }}>
            <Avatar style={{
              backgroundColor: glacierTheme.colors.primary,
              boxShadow: glacierTheme.shadows.sm,
            }} icon={<UserOutlined/>}/>
            <span style={{fontWeight: 500, color: glacierTheme.colors.text}}>{username}</span>
          </Space>
        </Dropdown>
      </Space>
    </Header>
  );
};

export default AppHeader;
