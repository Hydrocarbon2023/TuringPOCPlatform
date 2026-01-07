import React, { useState, useEffect } from 'react';
import { Tabs, Card, Table, Tag, Button, Modal, Form, Input, Select, message, Badge, theme, Descriptions, Skeleton } from 'antd';
import { PlusOutlined, ProjectOutlined } from '@ant-design/icons';
import { projectApi } from '../../api/api';

const UserDashboard = () => {
  const { token } = theme.useToken();
  const [projects, setProjects] = useState([]);
  const [isModalOpen, setIsModalOpen] = useState(false);

  // 详情弹窗状态
  const [detailModalOpen, setDetailModalOpen] = useState(false);
  const [currentProject, setCurrentProject] = useState(null);
  const [loadingDetail, setLoadingDetail] = useState(false);

  const [form] = Form.useForm();

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    try {
      const res = await projectApi.getAll();
      setProjects(res.data);
    } catch (error) {}
  };

  // 打开详情
  const handleViewDetail = async (id) => {
    setDetailModalOpen(true);
    setLoadingDetail(true);
    try {
      const res = await projectApi.getDetail(id);
      setCurrentProject(res.data);
    } catch (e) {
      message.error('获取详情失败');
    } finally {
      setLoadingDetail(false);
    }
  };

  // 提交申报
  const handleCreate = async (values) => {
    try {
      await projectApi.create(values);
      message.success('申报成功');
      setIsModalOpen(false);
      form.resetFields();
      loadData();
    } catch (e) {}
  };

  const columns = [
    { title: '项目名称', dataIndex: 'project_name' },
    { title: '状态', dataIndex: 'status', render: s => <Badge status={s === '复审中' ? 'processing' : 'default'} text={s} /> },
    {
      title: '操作',
      render: (_, record) => <Button type="link" onClick={() => handleViewDetail(record.project_id)}>查看详情</Button>,
    },
  ];

  return (
    <div>
      <div style={{ background: token.colorBgContainer, padding: 24, borderRadius: token.borderRadius, display: 'flex', justifyContent: 'space-between' }}>
        <h2>我的工作台</h2>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setIsModalOpen(true)}>申报新项目</Button>
      </div>

      <Card style={{ marginTop: 24, borderRadius: token.borderRadius }}>
        <Tabs items={[{ key: '1', label: <span><ProjectOutlined /> 我的项目</span>, children: <Table dataSource={projects} columns={columns} rowKey="project_id" /> }]} />
      </Card>

      {/* 1. 申报弹窗 (保持不变，省略代码以节省篇幅，沿用之前的即可) */}
      <Modal title="申报新项目" open={isModalOpen} onCancel={() => setIsModalOpen(false)} footer={null}>
        <Form form={form} layout="vertical" onFinish={handleCreate}>
          <Form.Item name="project_name" label="名称" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="domain" label="领域" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="maturity_level" label="成熟度" rules={[{ required: true }]}><Select options={[{value:'研发阶段',label:'研发阶段'}]} /></Form.Item>
          <Form.Item name="project_description" label="描述"><Input.TextArea /></Form.Item>
          <Button type="primary" htmlType="submit" block>提交</Button>
        </Form>
      </Modal>

      {/* 2. 详情弹窗 (新增) */}
      <Modal title="项目详情" open={detailModalOpen} onCancel={() => setDetailModalOpen(false)} footer={null} width={700}>
        {loadingDetail || !currentProject ? <Skeleton active /> : (
          <Descriptions bordered column={1}>
            <Descriptions.Item label="项目名称">{currentProject.project_name}</Descriptions.Item>
            <Descriptions.Item label="负责人">{currentProject.principal_name}</Descriptions.Item>
            <Descriptions.Item label="所属领域"><Tag color="blue">{currentProject.domain}</Tag></Descriptions.Item>
            <Descriptions.Item label="当前状态"><Tag color="geekblue">{currentProject.status}</Tag></Descriptions.Item>
            <Descriptions.Item label="成熟度">{currentProject.maturity_level}</Descriptions.Item>
            <Descriptions.Item label="提交时间">{currentProject.submit_time}</Descriptions.Item>
            <Descriptions.Item label="项目简介">{currentProject.project_description || '无'}</Descriptions.Item>
          </Descriptions>
        )}
      </Modal>
    </div>
  );
};

export default UserDashboard;
