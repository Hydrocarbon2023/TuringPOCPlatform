"""
认证相关API资源
"""
import logging
from flask import request
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from flask_restful import Resource

from models import db, User
from exceptions import ValidationError, NotFoundError, APIException
from utils import get_current_user

logger = logging.getLogger(__name__)


class Login(Resource):
    """用户登录"""
    def post(self):
        try:
            data = request.get_json()
            if not data or 'user_name' not in data or 'password' not in data:
                raise ValidationError('用户名和密码不能为空')

            user = User.query.filter_by(user_name=data['user_name']).first()
            if not user or not user.check_password(data['password']):
                raise ValidationError('用户名或密码错误')

            token = create_access_token(identity=str(user.user_id))
            return {
                'token': token,
                'user_id': user.user_id,
                'user_name': user.user_name,
                'real_name': user.real_name,
                'role': user.role
            }, 200
        except APIException:
            raise
        except Exception as e:
            logger.error(f"登录失败: {str(e)}", exc_info=True)
            raise APIException('登录失败，请稍后重试', 500)


class Register(Resource):
    """用户注册"""
    def post(self):
        try:
            data = request.get_json()
            if not data or 'user_name' not in data or 'password' not in data:
                raise ValidationError('用户名和密码不能为空')

            if User.query.filter_by(user_name=data['user_name']).first():
                raise ValidationError('用户名已存在')

            # 允许注册时选择角色
            allowed_roles = ['项目参与者', '评审人', '秘书', '企业支持者']
            role = data.get('role', '项目参与者')
            if role not in allowed_roles:
                role = '项目参与者'  # 默认角色

            new_user = User(
                user_name=data['user_name'],
                real_name=data.get('real_name'),
                role=role,
                affiliation=data.get('affiliation'),
                email=data.get('email')
            )
            new_user.set_password(data['password'])
            db.session.add(new_user)
            db.session.commit()
            return {'message': '注册成功'}, 201
        except APIException:
            raise
        except Exception as e:
            logger.error(f"注册失败: {str(e)}", exc_info=True)
            db.session.rollback()
            raise APIException('注册失败，请稍后重试', 500)
