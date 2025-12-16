import {ConfigProvider} from 'antd';
import React from 'react';
import {BrowserRouter as Router, Route, Routes} from 'react-router-dom';

function App() {
  return (
    <ConfigProvider theme={{token: {colorPrimary: '#1890ff'}}}>
      <Router>
        <Routes>
          <Route path="/" element={<Login/>}/>
          <Route path="/register" element={<Register/>}/>
          <Route path="/applicant/dashboard" element={<ApplicantDashboard/>}/>
          <Route path="/applicant/declare" element={<ProjectDeclare/>}/>
          <Route path="/projects/:id" element={<ProjectDetail/>}/>
          <Route path="/expert/review" element={<ExpertReview/>}/>
          <Route path="/admin/dashboard" element={<AdminDashboard/>}/>
          <Route path="/teams/create" element={<CreateTeam/>}/>
          <Route path="/teams/:id" element={<TeamDetail/>}/>
          <Route path="/teams/:id/join" element={<JoinTeam/>}/>
          <Route path="/notification" element={<NotificationList/>}/>
        </Routes>
      </Router>
    </ConfigProvider>
  );
}

export default App;
