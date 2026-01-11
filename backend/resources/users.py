"""
用户管理API资源
"""
import logging
from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource

from models import db, User
from exceptions import ValidationError, PermissionError, APIException
from utils import get_current_user

logger = logging.getLogger(__name__)


class AdminUserResource(Resource):
    """管理员用户管理"""
    @jwt_required()
    def post(self):
        """创建用户（仅管理员）"""
        try:
            current_user = get_current_user()
            if current_user.role != '管理员':
                raise PermissionError('只有管理员可以创建用户')

            data = request.get_json()
            if not data or 'user_name' not in data or 'password' not in data:
                raise ValidationError('用户名和密码不能为空')

            if User.query.filter_by(user_name=data['user_name']).first():
                raise ValidationError('用户名已存在')

            new_user = User(
                user_name=data['user_name'],
                real_name=data['real_name'],
                role=data['role'],
                affiliation=data.get('affiliation'),
                email=data.get('email')
            )
            new_user.set_password(data['password'])
            db.session.add(new_user)
            db.session.commit()
            return {'message': f'已创建用户: {data["real_name"]}'}, 201
        except APIException:
            raise
        except Exception as e:
            logger.error(f"创建用户失败: {str(e)}", exc_info=True)
            db.session.rollback()
            raise APIException('创建用户失败，请稍后重试', 500)

    @jwt_required()
    def get(self):
        """获取所有用户列表（管理员/秘书可见）"""
        try:
            current_user = get_current_user()
            if current_user.role not in ['管理员', '秘书']:
                raise PermissionError('只有管理员或秘书可以查看用户列表')

            users = User.query.all()
            return [{
                'user_id': u.user_id,
                'user_name': u.user_name,
                'real_name': u.real_name,
                'role': u.role,
                'affiliation': u.affiliation
            } for u in users]
        except APIException:
            raise
        except Exception as e:
            logger.error(f"获取用户列表失败: {str(e)}", exc_info=True)
            raise APIException('获取用户列表失败，请稍后重试', 500)
