import React, {useState, useEffect} from 'react';
import {Table, Card, Button, Tag, Modal, Radio, Input, message, Select, DatePicker, Form, Space, theme} from 'antd';
import {AuditOutlined, SendOutlined} from '@ant-design/icons';
import {projectApi, commonApi} from '../../api/api';

const SecretaryDashboard = () => {
  const {token} = theme.useToken();
  const [projects, setProjects] = useState([]);
  const [users, setUsers] = useState([]);
  const [auditModal, setAuditModal] = useState({open: false, projectId: null});
  const [assignModal, setAssignModal] = useState({open: false, projectId: null});
  const [auditResult, setAuditResult] = useState('通过');
  const [comment, setComment] = useState('');
  const [assignForm] = Form.useForm();

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const pRes = await projectApi.getAll();
      setProjects(pRes.data);
      const uRes = await commonApi.getAllUsers();
      setUsers(uRes.data);
    } catch (e) {
    }
  };

  const handleAudit = async () => {
    try {
      await projectApi.audit(auditModal.projectId, {result: auditResult, comment});
      message.success('初审完成');
      setAuditModal({open: false, projectId: null});
      loadData();
    } catch (e) {
    }
  };

  const handleAssign = async (values) => {
    try {
      await projectApi.assignExpert(assignModal.projectId, {
        expert_id: values.expert_id,
        deadline: values.deadline?.format('YYYY-MM-DD')
      });
      message.success('已分配专家');
      setAssignModal({open: false, projectId: null});
      assignForm.resetFields();
    } catch (e) {
    }
  };

  const columns = [
    {title: '项目名称', dataIndex: 'project_name', render: t => <b>{t}</b>},
    {title: '申请人', dataIndex: 'principal_name'},
    {
      title: '状态',
      dataIndex: 'status',
      render: s => <Tag color={s === '复审中' ? 'blue' : (s === '待初审' ? 'orange' : 'default')}>{s}</Tag>
    },
    {
      title: '操作',
      render: (_, record) => (
        <Space>
          {record.status === '待初审' && (
            <Button type="primary" size="small" icon={<AuditOutlined/>}
                    onClick={() => setAuditModal({open: true, projectId: record.project_id})}>初审</Button>
          )}
          {record.status === '复审中' && (
            <Button size="small" icon={<SendOutlined/>}
                    onClick={() => setAssignModal({open: true, projectId: record.project_id})}>分配</Button>
          )}
        </Space>
      ),
    },
  ];

  return (
    <Card title="秘书控制台" style={{borderRadius: token.borderRadius}}>
      <Button onClick={loadData} style={{marginBottom: 16}}>刷新列表</Button>
      <Table dataSource={projects} columns={columns} rowKey="project_id"/>

      <Modal title="项目初审" open={auditModal.open} onOk={handleAudit} onCancel={() => setAuditModal({open: false})}>
        <Radio.Group value={auditResult} onChange={e => setAuditResult(e.target.value)} style={{marginBottom: 16}}>
          <Radio.Button value="通过">通过</Radio.Button>
          <Radio.Button value="未通过">驳回</Radio.Button>
        </Radio.Group>
        <Input.TextArea rows={3} placeholder="意见" value={comment} onChange={e => setComment(e.target.value)}/>
      </Modal>

      <Modal title="分配专家" open={assignModal.open} footer={null} onCancel={() => setAssignModal({open: false})}>
        <Form form={assignForm} onFinish={handleAssign} layout="vertical">
          <Form.Item name="expert_id" label="专家" rules={[{required: true}]}>
            <Select showSearch optionFilterProp="label">
              {users.filter(u => u.role === '评审人').map(u => (
                <Select.Option key={u.user_id} value={u.user_id} label={u.real_name}>{u.real_name}</Select.Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item name="deadline" label="截止日期"><DatePicker style={{width: '100%'}}/></Form.Item>
          <Button type="primary" htmlType="submit" block>分配</Button>
        </Form>
      </Modal>
    </Card>
  );
};

export default SecretaryDashboard;
