import {App as AntdApp, ConfigProvider, Layout, theme} from 'antd';
import React from 'react';
import {BrowserRouter as Router, Navigate, Route, Routes} from 'react-router-dom';

import AppHeader from './components/AppHeader';
import Dashboard from './pages/Dashboard';
import Login from './pages/Login';
import Register from './pages/Register';
import IncubationDashboard from './pages/incubation/IncubationDashboard';

const {Content} = Layout;

import {glacierTheme} from './styles/theme';

const modernTheme = {
  token: {
    colorPrimary: glacierTheme.colors.primary,
    borderRadius: 12,
    colorBgContainer: glacierTheme.colors.surface,
    colorBgBase: glacierTheme.colors.background,
    colorText: glacierTheme.colors.text,
    colorTextSecondary: glacierTheme.colors.textSecondary,
    fontFamily: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
    boxShadow: glacierTheme.shadows.md,
    boxShadowSecondary: glacierTheme.shadows.sm,
  },
  algorithm: theme.defaultAlgorithm,
};

function App() {
  return (
    <ConfigProvider theme={modernTheme}>
      <AntdApp>
        <Router>
          <Layout style={{
            minHeight: '100vh',
            background: `linear-gradient(135deg, ${glacierTheme.colors.background} 0%, ${glacierTheme.colors.surface} 50%, ${glacierTheme.colors.primaryLight}20 100%)`,
            position: 'relative',
          }}>
            <Routes>
              <Route path="/register" element={<Register/>}/>
              <Route path="/login" element={<Login/>}/>
              <Route
                path="/*"
                element={
                  <>
                    <AppHeader/>
                    <Content style={{
                      padding: `${glacierTheme.spacing.xl} ${glacierTheme.spacing.xxl}`,
                      maxWidth: 1400,
                      margin: '0 auto',
                      width: '100%',
                    }}>
                      <Routes>
                        <Route path="/" element={<Navigate to="/login"/>}/>
                        <Route path="/dashboard" element={<Dashboard/>}/>
                        <Route path="/incubation/:projectId" element={<IncubationDashboard/>}/>
                      </Routes>
                    </Content>
                  </>
                }
              />
            </Routes>
          </Layout>
        </Router>
      </AntdApp>
    </ConfigProvider>
  );
}

export default App;
