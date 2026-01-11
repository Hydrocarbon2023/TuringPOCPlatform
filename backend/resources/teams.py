"""
团队管理API资源
"""
import logging
from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_restful import Resource
from sqlalchemy import func

from models import db, User, Team, UserInTeam
from exceptions import ValidationError, NotFoundError, PermissionError, APIException
from utils import get_current_user

logger = logging.getLogger(__name__)


class TeamResource(Resource):
    """团队管理"""
    @jwt_required()
    def get(self):
        """获取所有团队列表 (管理员/秘书可见)"""
        try:
            current_user = get_current_user()
            if current_user.role not in ['管理员', '秘书']:
                raise PermissionError('只有管理员或秘书可以查看所有团队')

            # 优化：使用JOIN一次性获取leader信息，使用聚合查询获取成员数量
            results = db.session.query(
                Team,
                User.user_name.label('leader_name'),
                func.count(UserInTeam.user_id).label('member_count')
            ).outerjoin(User, Team.leader_id == User.user_id)\
            .outerjoin(UserInTeam, Team.team_id == UserInTeam.team_id)\
            .group_by(Team.team_id, User.user_name).all()

            return [{
                'team_id': t.Team.team_id,
                'team_name': t.Team.team_name,
                'domain': t.Team.domain,
                'leader_id': t.Team.leader_id,
                'leader_name': t.leader_name or '未知',
                'member_count': t.member_count or 0
            } for t in results]
        except APIException:
            raise
        except Exception as e:
            logger.error(f"获取团队列表失败: {str(e)}", exc_info=True)
            raise APIException('获取团队列表失败，请稍后重试', 500)

    @jwt_required()
    def post(self):
        """创建团队"""
        try:
            uid = get_jwt_identity()
            data = request.get_json()
            if not data or 'team_name' not in data:
                raise ValidationError('团队名称不能为空')

            new_team = Team(
                team_name=data['team_name'],
                domain=data.get('domain'),
                leader_id=uid
            )
            db.session.add(new_team)
            db.session.flush()  # 获取team_id

            # 自动将创建者加入团队
            user_in_team = UserInTeam(user_id=uid, team_id=new_team.team_id)
            db.session.add(user_in_team)
            db.session.commit()

            return {'message': '团队创建成功', 'team_id': new_team.team_id}, 201
        except APIException:
            raise
        except Exception as e:
            logger.error(f"创建团队失败: {str(e)}", exc_info=True)
            db.session.rollback()
            raise APIException('创建团队失败，请稍后重试', 500)


class MyTeamsResource(Resource):
    """获取当前用户所属的团队信息"""
    @jwt_required()
    def get(self):
        try:
            uid = get_jwt_identity()
            # 优化：使用JOIN一次性获取leader信息，避免N+1查询
            results = db.session.query(Team, User.user_name.label('leader_name')) \
                .join(UserInTeam, Team.team_id == UserInTeam.team_id) \
                .outerjoin(User, Team.leader_id == User.user_id) \
                .filter(UserInTeam.user_id == uid).all()
            
            return [{
                'team_id': t.Team.team_id,
                'team_name': t.Team.team_name,
                'domain': t.Team.domain,
                'role': '队长' if str(t.Team.leader_id) == str(uid) else '成员',
                'leader_name': leader_name or '未知'
            } for t, leader_name in results]
        except APIException:
            raise
        except Exception as e:
            logger.error(f"获取我的团队列表失败: {str(e)}", exc_info=True)
            raise APIException('获取团队列表失败，请稍后重试', 500)


class TeamMembersResource(Resource):
    """团队成员管理"""
    @jwt_required()
    def post(self, team_id):
        """邀请成员加入团队（仅队长）"""
        try:
            current_uid = get_jwt_identity()
            team = Team.query.get_or_404(team_id)
            if str(team.leader_id) != str(current_uid):
                raise PermissionError('只有队长可以邀请成员')

            data = request.get_json()
            if not data or 'user_name' not in data:
                raise ValidationError('用户名不能为空')
            
            target_username = data.get('user_name')
            target_user = User.query.filter_by(user_name=target_username).first()

            if not target_user:
                raise NotFoundError('用户不存在')

            exists = UserInTeam.query.filter_by(user_id=target_user.user_id, team_id=team_id).first()
            if exists:
                raise ValidationError('该用户已在团队中')

            new_member = UserInTeam(user_id=target_user.user_id, team_id=team_id)
            db.session.add(new_member)
            db.session.commit()
            return {'message': f'已邀请 {target_user.real_name} 加入团队'}, 201
        except APIException:
            raise
        except Exception as e:
            logger.error(f"邀请团队成员失败: {str(e)}", exc_info=True)
            db.session.rollback()
            raise APIException('邀请成员失败，请稍后重试', 500)

    @jwt_required()
    def get(self, team_id):
        """获取团队成员列表"""
        try:
            team = Team.query.get_or_404(team_id)
            members = db.session.query(User).join(UserInTeam).filter(UserInTeam.team_id == team_id).all()
            return [{
                'user_id': u.user_id,
                'user_name': u.user_name,
                'real_name': u.real_name,
                'role': '队长' if u.user_id == team.leader_id else '成员'
            } for u in members]
        except APIException:
            raise
        except Exception as e:
            logger.error(f"获取团队成员列表失败: {str(e)}", exc_info=True)
            raise APIException('获取成员列表失败，请稍后重试', 500)
