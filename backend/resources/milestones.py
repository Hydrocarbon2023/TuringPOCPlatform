"""
里程碑管理API资源
"""
import logging
from datetime import datetime
from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_restful import Resource

from models import db, User, UserInTeam, Project, Milestone
from exceptions import ValidationError, PermissionError, APIException
from utils import get_current_user

logger = logging.getLogger(__name__)


class ProjectMilestonesResource(Resource):
    """项目里程碑列表"""
    @jwt_required()
    def get(self, project_id):
        """获取项目的里程碑列表"""
        try:
            uid = get_jwt_identity()
            project = Project.query.get_or_404(project_id)
            
            # 权限检查：项目成员、管理员、秘书可见
            has_permission = False
            if str(project.principal_id) == str(uid):
                has_permission = True
            else:
                my_team_ids = db.session.query(UserInTeam.team_id).filter_by(user_id=uid).all()
                my_team_ids = [tid[0] for tid in my_team_ids]
                if project.team_id in my_team_ids:
                    has_permission = True
                else:
                    user = User.query.get(uid)
                    if user and user.role in ['管理员', '秘书']:
                        has_permission = True
            
            if not has_permission:
                raise PermissionError('无权查看此项目的里程碑信息')
            
            milestones = Milestone.query.filter_by(project_id=project_id).order_by(
                Milestone.due_date.asc()
            ).all()
            
            return [{
                'milestone_id': m.milestone_id,
                'project_id': m.project_id,
                'title': m.title,
                'due_date': str(m.due_date) if m.due_date else None,
                'status': m.status,
                'deliverable': m.deliverable or '',
                'create_time': str(m.create_time),
                'update_time': str(m.update_time)
            } for m in milestones]
        except APIException:
            raise
        except Exception as e:
            logger.error(f"获取里程碑列表失败: {str(e)}", exc_info=True)
            raise APIException('获取里程碑列表失败，请稍后重试', 500)


class MilestoneUpdateResource(Resource):
    """里程碑更新"""
    @jwt_required()
    def put(self, milestone_id):
        """更新里程碑状态（仅项目负责人）"""
        try:
            uid = get_jwt_identity()
            milestone = Milestone.query.get_or_404(milestone_id)
            project = Project.query.get_or_404(milestone.project_id)
            
            # 权限检查：只有项目负责人可以更新里程碑
            if str(project.principal_id) != str(uid):
                raise PermissionError('只有项目负责人可以更新里程碑状态')
            
            data = request.get_json()
            if not data:
                raise ValidationError('更新数据不能为空')
            
            # 更新状态
            if 'status' in data:
                if data['status'] not in ['未开始', '进行中', '已完成']:
                    raise ValidationError('状态值无效')
                milestone.status = data['status']
            
            # 更新交付物描述
            if 'deliverable' in data:
                milestone.deliverable = data['deliverable']
            
            # 更新截止日期
            if 'due_date' in data and data['due_date']:
                try:
                    milestone.due_date = datetime.strptime(data['due_date'], '%Y-%m-%d')
                except (ValueError, TypeError):
                    raise ValidationError('日期格式错误，应为 YYYY-MM-DD')
            
            milestone.update_time = datetime.now()
            db.session.commit()
            
            return {'message': '里程碑更新成功'}
        except APIException:
            raise
        except Exception as e:
            logger.error(f"更新里程碑失败: {str(e)}", exc_info=True)
            db.session.rollback()
            raise APIException('更新里程碑失败，请稍后重试', 500)
