"""
评论管理API资源
"""
import logging
from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_restful import Resource

from models import db, User, UserInTeam, Project, ReviewTask, IncubationComment
from exceptions import ValidationError, PermissionError, APIException
from utils import get_current_user

logger = logging.getLogger(__name__)


class ProjectCommentsResource(Resource):
    """项目沟通留言"""
    @jwt_required()
    def get(self, project_id):
        """获取项目的留言列表"""
        try:
            uid = get_jwt_identity()
            project = Project.query.get_or_404(project_id)
            
            # 权限检查：项目负责人、团队成员、曾评审过该项目的评审人
            has_permission = False
            if str(project.principal_id) == str(uid):
                has_permission = True
            else:
                # 检查是否为团队成员
                my_team_ids = db.session.query(UserInTeam.team_id).filter_by(user_id=uid).all()
                my_team_ids = [tid[0] for tid in my_team_ids]
                if project.team_id in my_team_ids:
                    has_permission = True
                else:
                    # 检查是否为曾评审过该项目的评审人
                    reviewed = ReviewTask.query.filter_by(
                        project_id=project_id,
                        reviewer_id=uid
                    ).first()
                    if reviewed:
                        has_permission = True
            
            if not has_permission:
                raise PermissionError('无权查看此项目的留言')
            
            # 获取所有留言，包含用户信息
            comments = db.session.query(IncubationComment, User.real_name, User.role, User.affiliation)\
                .join(User, IncubationComment.user_id == User.user_id)\
                .filter(IncubationComment.project_id == project_id)\
                .order_by(IncubationComment.create_time.asc()).all()
            
            return [{
                'comment_id': c.IncubationComment.comment_id,
                'project_id': c.IncubationComment.project_id,
                'user_id': c.IncubationComment.user_id,
                'content': c.IncubationComment.content,
                'parent_id': c.IncubationComment.parent_id,
                'create_time': str(c.IncubationComment.create_time),
                'user_name': c.real_name or '未知',
                'user_role': c.role,
                'user_affiliation': c.affiliation or ''
            } for c in comments]
        except APIException:
            raise
        except Exception as e:
            logger.error(f"获取留言列表失败: {str(e)}", exc_info=True)
            raise APIException('获取留言列表失败，请稍后重试', 500)
    
    @jwt_required()
    def post(self, project_id):
        """发表留言"""
        try:
            uid = get_jwt_identity()
            project = Project.query.get_or_404(project_id)
            
            # 权限检查：项目负责人、团队成员、曾评审过该项目的评审人
            has_permission = False
            if str(project.principal_id) == str(uid):
                has_permission = True
            else:
                my_team_ids = db.session.query(UserInTeam.team_id).filter_by(user_id=uid).all()
                my_team_ids = [tid[0] for tid in my_team_ids]
                if project.team_id in my_team_ids:
                    has_permission = True
                else:
                    reviewed = ReviewTask.query.filter_by(
                        project_id=project_id,
                        reviewer_id=uid
                    ).first()
                    if reviewed:
                        has_permission = True
            
            if not has_permission:
                raise PermissionError('无权在此项目留言')
            
            data = request.get_json()
            if not data or not data.get('content'):
                raise ValidationError('留言内容不能为空')
            
            comment = IncubationComment(
                project_id=project_id,
                user_id=uid,
                content=data['content'],
                parent_id=data.get('parent_id')  # 可选，用于回复
            )
            db.session.add(comment)
            db.session.commit()
            
            return {'message': '留言发表成功', 'comment_id': comment.comment_id}, 201
        except APIException:
            raise
        except Exception as e:
            logger.error(f"发表留言失败: {str(e)}", exc_info=True)
            db.session.rollback()
            raise APIException('发表留言失败，请稍后重试', 500)
