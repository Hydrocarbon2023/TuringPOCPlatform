import {Button, Form, Input, message, Select} from 'antd';
import React, {useState} from 'react';
import {useNavigate} from 'react-router-dom';

import api from '../api/api';

const Register = () => {
  const [loading, setLoading] = userState(false);
  const navigate = useNavigate();

  const onFinish = async (values) => {
    setLoading(true);
    try {
      await api.post('/register', values);
      message.success('注册成功！');
      navigate('/');
    } catch (err) {
      message.error('出错了，注册失败TT');
    }
    setLoading(false);
  };

  return (
    <div style={{display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh'}}>
      <Form onFinish={onFinish} style={{width: 400}}>
        <Form.Item name="user_name" rules={[{required: true}]}>
          <Input placeholder="用户名"/>
        </Form.Item>
        <Form.Item name="password" rules={[{required: true}]}>
          <Input.Password placeholder="密码"/>
        </Form.Item>
        <Form.Item name="role" rules={[{required: true}]}>
          <Select placeholder="身份">
            <Select.Option value="项目参与者">项目参与者</Select.Option>
            <Select.Option value="评审人">评审人</Select.Option>
            <Select.Option value="秘书">秘书</Select.Option>
            <Select.Option value="管理员">管理员</Select.Option>
          </Select>
        </Form.Item>
        <Form.Item name="affiliation">
          <Input placeholder="所属单位"/>
        </Form.Item>
        <Form.Item name="email">
          <Input placeholder="邮箱"/>
        </Form.Item>
        <Form.Item>
          <Input.TextArea placeholder="个人简介"/>
        </Form.Item>
        <Form.Item>
          <Button type="primary" htmlType="submit" loading={loading} block>
            注册
          </Button>
        </Form.Item>
      </Form>
    </div>
  );
};

export default Register;
