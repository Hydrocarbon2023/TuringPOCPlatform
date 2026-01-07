import React, {useState, useEffect} from 'react';
import {Tabs, Card, Table, Tag, Button, Modal, Form, Input, Select, message, Badge} from 'antd';
import {PlusOutlined, BellOutlined} from '@ant-design/icons';
import {projectApi, commonApi} from '../../api/api';

const UserDashboard = () => {
  const [projects, setProjects] = useState([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [form] = Form.useForm();

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const res = await projectApi.getAll(); // 实际应调用 getMyProjects
      setProjects(res.data);
    } catch (error) {
      console.error(error);
    }
  };

  const handleCreate = async (values) => {
    try {
      await projectApi.create(values);
      message.success('项目申报提交成功！');
      setIsModalOpen(false);
      form.resetFields();
      loadData();
    } catch (error) {}
  };

  const columns = [
    {title: '项目名称', dataIndex: 'project_name', key: 'name'},
    {title: '领域', dataIndex: 'domain', key: 'domain', render: text => <Tag color="blue">{text}</Tag>},
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: status => {
        const colorMap = {'待初审': 'orange', '已通过': 'green', '已取消': 'red', '初审中': 'processing'};
        return <Badge status={colorMap[status] || 'default'} text={status} />;
      }
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Button type="link" size="small">查看详情</Button>
      ),
    },
  ];

  return (
    <div>
      <div style={{display: 'flex', justifyContent: 'space-between', marginBottom: 24}}>
        <h2 style={{margin: 0}}>我的工作台</h2>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setIsModalOpen(true)}>
          申报新项目
        </Button>
      </div>

      <Tabs defaultActiveKey="1" items={[
        {
          key: '1',
          label: '我的项目',
          children: (
            <Card bordered={false} className="shadow-sm">
              <Table dataSource={projects} columns={columns} rowKey="project_id"/>
            </Card>
          ),
        },
        {
          key: '2',
          label: <span><BellOutlined /> 消息通知</span>,
          children: <Card>暂无新消息</Card>
        }
      ]} />

      <Modal title="申报新项目" open={isModalOpen} onCancel={() => setIsModalOpen(false)} footer={null}>
        <Form form={form} layout="vertical" onFinish={handleCreate}>
          <Form.Item name="project_name" label="项目名称" rules={[{required: true}]}>
            <Input placeholder="请输入项目全称" />
          </Form.Item>
          <Form.Item name="domain" label="所属领域" rules={[{required: true }]}>
            <Select options={[
              { value: '人工智能', label: '人工智能' },
              { value: '生物医药', label: '生物医药' },
              { value: '新能源', label: '新能源' },
            ]} />
          </Form.Item>
          <Form.Item name="maturity_level" label="成熟度" rules={[{required: true}]}>
            <Select options={[
              {value: '研发阶段', label: '研发阶段'},
              {value: '小试阶段', label: '小试阶段'},
            ]} />
          </Form.Item>
          <Form.Item name="project_description" label="项目简介">
            <Input.TextArea rows={4} />
          </Form.Item>
          <Button type="primary" htmlType="submit" block>提交申报</Button>
        </Form>
      </Modal>
    </div>
  );
};

export default UserDashboard;
