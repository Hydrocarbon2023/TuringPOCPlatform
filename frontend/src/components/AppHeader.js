import {LogoutOutlined, UserOutlined} from '@ant-design/icons';
import {Avatar, Dropdown, Layout, Space, theme} from 'antd';
import React from 'react';
import {useNavigate} from 'react-router-dom';

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
      background: token.colorBgContainer,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
      padding: '0 24px',
      position: 'sticky',
      top: 0,
      zIndex: 100
    }}>
      <div style={{fontSize: '20px', fontWeight: 'bold', color: token.colorPrimary}}>
        🚀 图灵数智概念验证平台
      </div>
      <Space>
        <span style={{color: '#666'}}>{role}</span>
        <Dropdown menu={{items}} placement="bottomRight">
          <Space style={{cursor: 'pointer'}}>
            <Avatar style={{backgroundColor: token.colorPrimary}} icon={<UserOutlined/>}/>
            <span style={{fontWeight: 500}}>{username}</span>
          </Space>
        </Dropdown>
      </Space>
    </Header>
  );
};

export default AppHeader;
