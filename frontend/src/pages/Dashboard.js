import {CheckCircleOutlined, CloseCircleOutlined, FormOutlined, PlusOutlined} from '@ant-design/icons';
import {Button, Card, Descriptions, Form, Input, InputNumber, message, Modal, Select, Table, Tabs, Tag,
        Typography} from 'antd';
import React, {useEffect, useState} from 'react';

import api from '../api/api';

const {Option} = Select;
const {TextArea} = Input;

const Dashboard = () => {
  const role = localStorage.getItem('role');
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [currentAction, setCurrentAction] = useState('');
  const [selectedRecord, setSelectedRecord] = useState(null);
  const [form] = Form.useForm();
  const [teams, setTeams] = useState([]);
  const [allUsers, setAllUsers] = useState([]);

  const fetchData = async () => {
    setLoading(true);
    try {
      let res;
      if (role === '项目参与者') {
        res = await api.get('/projects');
      } else if (role === '秘书') {
        res = await api.get('/reviews/tasks');
      }
      setData(res.data || []);
    } catch (err) {
      message.error('获取数据失败TT');
    } finally {
      setLoading(false);
    }
  };

  const fetchTeams = async () => {
    try {
      const res = await api.get('/teams');
      setTeams(res.data);
    } catch (err) {
      message.error('获取团队列表失败TT');
    }
  };

  useEffect(() => {
    fetchData();
  }, [role]);

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();

      if (currentAction === 'create') {
        await api.post('/projects', {...values, team_id: 1});
        message.success('项目申报成功！')
      } else if (currentAction === 'audit') {
        await api.post(`/projects/${selectedRecord.project_id}/audit`, {
          result: values.result,
          comment: values.comment
        });
        message.success('初审结果已提交！');
      } else if (currentAction === 'review') {
        await api.post(`/reviews/tasks/${selectedRecord.task_id}/opinion`, values);
        message.success('评审意见已提交！');
      } else if (currentAction === 'createTeam') {
        await api.post('/teams', values);
        message.success('团队创建成功！');
        fetchTeams();
      }

      setModalVisible(false);
      form.resetFields();
      if (currentAction !== 'createTeam') fetchData();
    } catch (err) {
      message.error('出了点问题，请重试TT');
    }
  };

  // 项目参与者视图
  const participantColumns = [
    {title: '项目名称', dataIndex: 'project_name', key: 'project_name'},
    {title: '领域', dataIndex: 'domain', key: 'domain'},
    {title: '成熟度', dataIndex: 'maturity_level', key: 'maturity_level'},
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: status => {
        let color = status === '已通过' ? 'green' : (status === '已取消' ? 'red' : 'blue');
        return <Tag color={color}>{status || '未知'}</Tag>;
      }
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Button type='link' onClick={() => message.info('详情功能待开发')}>查看详情</Button>
      )
    }
  ];

  // 秘书视图
  const secretaryColumns = [
    {title: '项目ID', dataIndex: 'project_id', key: 'project_id'},
    {title: '项目名称', dataIndex: 'project_name', key: 'project_name'},
    {
      title: '当前状态',
      dataIndex: 'status',
      key: 'status',
      render: status => <Tag color="orange">{status}</Tag>
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        record.status === '待初审' ? (
          <Button type='primary' size='small' onClick={() => {
            setSelectedRecord(record);
            setCurrentAction('audit');
            setModalVisible(true);
          }}>
            审核
          </Button>
        ) : <Button disabled size='small'>已处理</Button>
      ),
    },
  ];

  // 评审人视图
  const expertColumns = [
    {title: '任务ID', dataIndex: 'task_id', key: 'task_id'},
    {title: '项目名称', dataIndex: 'project_name', key: 'project_name'},
    {title: '截止时间', dataIndex: 'deadline', key: 'deadline'},
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: status => <Tag color={status === '已完成' ? 'green' : 'processing'}>{status}</Tag>
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        record.status !== '已完成' && (
          <Button type='primary' ghost size='small' icon={<FormOutlined/>} onClick={() => {
            setSelectedRecord(record);
            setCurrentAction('review');
            setModalVisible(true);
          }}>
            开始评审
          </Button>
        )
      ),
    },
  ];

  const items = [
    {
      key: 'projects',
      label: '管理项目',
      children: (
        <Card title='项目列表' extra={role === '项目参与者' &&
          <Button onClick={() => {
            setCurrentAction('create');
            setModalVisible(true);
          }}>
            申报项目
          </Button>
        }>
          <Table dataSource={data} columns={role === '项目参与者' ? participantColumns : secretaryColumns}/>
        </Card>
      ),
    },
    {
      key: 'teams',
      label: '管理团队',
      children: (
        <Card title='我的团队' extra={
          <Button icon={<PlusOutlined/>} onClick={() => {
            setCurrentAction('createTeam');
            setModalVisible(true);
          }}>
            创建团队
          </Button>
        }>
          <Table dataSource={teams}
            columns={[
              {title: '团队名称', dataIndex: 'team_name'},
              {title: '领域', dataIndex: 'domain'},
              {title: '操作', render: (_, r) => <Button type='link'>查看/邀请</Button>},
            ]}
          />
        </Card>
      ),
    },
    role === '管理员' && {
      key: 'admin',
      label: '系统后台',
      children: (
        <Card title='所有用户'>
          <Table dataSource={allUsers} columns={[
            {title: '用户名', dataIndex: 'user_name'},
            {title: '角色', dataIndex: 'role'},
          ]}/>
        </Card>
      ),
    },
  ].filter(Boolean);

  const renderModalContent = () => {
    if (currentAction === 'create') {
      return (
        <>
          <Form.Item name='project_name' label='项目名称' rules={[{required: true}]}>
            <Input/>
          </Form.Item>
          <Form.Item name='domain' label='所属领域' rules={[{required: true}]}>
            <Select>
              <Option value='人工智能'>人工智能</Option>
              <Option value='生物医药'>生物医药</Option>
              <Option value='新材料'>新材料</Option>
              <Option value='电子信息'>电子信息</Option>
            </Select>
          </Form.Item>
          <Form.Item name='maturity_level' label='成熟度' rules={[{required: true}]}>
            <Select>
              <Option value='研发阶段'>研发阶段</Option>
              <Option value='小试阶段'>小试阶段</Option>
              <Option value='中试阶段'>中试阶段</Option>
              <Option value='小批量生产阶段'>小批量生产阶段</Option>
            </Select>
          </Form.Item>
          <Form.Item name='project_description' label='项目简介'>
            <TextArea rows={5}/>
          </Form.Item>
        </>
      );
    }

    if (currentAction === 'audit') {
      return (
        <>
          <Descriptions title='项目信息' bordered size='small' column={1} style={{marginBottom: 20}}>
            <Descriptions.Item label='项目名称'>{selectedRecord?.project_name}</Descriptions.Item>
          </Descriptions>
          <Form.Item name='result' label='审核结果' rules={[{required: true}]}>
            <Select placeholder='请选择'>
              <Option value='通过'>通过</Option>
              <Option value='驳回'>驳回</Option>
            </Select>
          </Form.Item>
          <Form.Item name='comment' label='审核意见'>
            <TextArea rows={3} placeholder='请输入具体的审核意见'/>
          </Form.Item>
        </>
      );
    }

    if (currentAction === 'review') {
      return (
        <>
          <div style={{marginBottom: 16, color: '#666'}}>
            请对<strong>{selectedRecord?.project_name}</strong>进行打分（0-10分）
          </div>
          <Form.Item name='innovation_score' label='创新性' rules={[{required: true}]}>
            <InputNumber min={0} max={10} style={{width: '100%'}}/>
          </Form.Item>
          <Form.Item name='potentiality_score' label='市场潜力' rules={[{required: true}]}>
            <InputNumber min={0} max={10} style={{width: '100%'}}/>
          </Form.Item>
          <Form.Item name='feasibility_score' label='可行性' rules={[{required: true}]}>
            <InputNumber min={0} max={10} style={{width: '100%'}}/>
          </Form.Item>
          <Form.Item name='teamwork_score' label='团队能力' rules={[{required: true}]}>
            <InputNumber min={0} max={10} style={{width: '100%'}}/>
          </Form.Item>
          <Form.Item name='comment' label='综合评价'>
            <TextArea rows={4}/>
          </Form.Item>
        </>
      );
    }

    if (currentAction === 'createTeam') {
      return (
        <>
          <Form.Item name='team_name' label='团队名称' rules={[{
            required: true, message: '请输入团队名称'
          }]}>
            <Input placeholder='例如：419生命科学实验室'/>
          </Form.Item>
          <Form.Item name='domain' label='研究领域' rules={[{
            required: true, message: '请选择研究领域'
          }]}>
            <Input placeholder='例如：计算机图形学、金融工程'/>
          </Form.Item>
          <Form.Item name='team_profile' label='团队简介'>
            <TextArea rows={4} placeholder='介绍一下团队吧！'/>
          </Form.Item>
        </>
      );
    }
  };

  return (
    <div style={{padding: '20px'}}>
      <Tabs defaultActiveKey='projects' items={items}
        style={{background: '#fff', padding: '20px', borderRadius: '8px'}}
      />
      <Modal
        title={
          currentAction === 'create' ? '申报项目' :
            (currentAction === 'audit' ? '项目初审' :
              (currentAction === 'review' ? '项目复审' : '创建团队'))
        }
        open={modalVisible}
        onOk={handleSubmit}
        onCancel={() => setModalVisible(false)}
        destroyOnHidden={true}
      >
        <Form form={form} layout='verttical'>
          {renderModalContent()}
        </Form>
      </Modal>
    </div>
  );
};

export default Dashboard;
