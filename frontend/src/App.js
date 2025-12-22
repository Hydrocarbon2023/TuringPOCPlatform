import {App as AntdApp, ConfigProvider, Layout, theme} from 'antd';
import React from 'react';
import {BrowserRouter as Router, Navigate, Route, Routes} from 'react-router-dom';

import AppHeader from './components/AppHeader';
import Dashboard from './pages/Dashboard';
import Login from './pages/Login';
import Register from './pages/Register';

const {Content} = Layout;

const modernTheme = {
  token: {
    colorPrimary: '#AFCDD7',
    borderRadius: 12,
    colorBgContainer: '#DAE7E6',
    fontFamily: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
  },
  algorithm: theme.defaultAlgorithm,
};

function App() {
  return (
    <ConfigProvider theme={modernTheme}>
      <AntdApp>
        <Router>
          <Layout style={{minHeight: '100vh', background: '#F5F5F5'}}>
            <Routes>
              <Route path="/register" element={<Register/>}/>
              <Route path="/login" element={<Login/>}/>
              <Route
                path="/*"
                element={
                  <>
                    <AppHeader/>
                    <Content style={{padding: '24px 50px', maxWidth: 1200, margin: '0 auto', width: '100%'}}>
                      <Routes>
                        <Route path="/" element={<Navigate to="/login"/>}/>
                        <Route path="/dashboard" element={<Dashboard/>}/>
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
