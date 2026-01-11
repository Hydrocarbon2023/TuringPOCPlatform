"""
成果管理API资源
"""
import logging
from datetime import datetime
from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_restful import Resource

from models import db, User, UserInTeam, Project, Achievement, AchievementOfProject
from exceptions import ValidationError, PermissionError, APIException
from utils import get_current_user

logger = logging.getLogger(__name__)


class AchievementResource(Resource):
    """成果管理"""
    @jwt_required()
    def post(self):
        """上传成果"""
        try:
            uid = get_jwt_identity()
            data = request.get_json()
            
            if not data or not data.get('title') or not data.get('project_id'):
                raise ValidationError('成果标题和项目ID不能为空')
            
            project = Project.query.get_or_404(data['project_id'])
            
            # 权限检查：只有项目成员可以上传成果
            is_member = False
            if str(project.principal_id) == str(uid):
                is_member = True
            else:
                my_team_ids = db.session.query(UserInTeam.team_id).filter_by(user_id=uid).all()
                my_team_ids = [tid[0] for tid in my_team_ids]
                if project.team_id in my_team_ids:
                    is_member = True
            
            if not is_member:
                raise PermissionError('只有项目成员可以上传成果')
            
            # 解析发布时间
            publish_time = datetime.now()
            if data.get('publish_time'):
                try:
                    publish_time = datetime.strptime(data['publish_time'], '%Y-%m-%d')
                except (ValueError, TypeError):
                    logger.warning(f"发布时间格式解析失败: {data.get('publish_time')}")
            
            # 创建成果记录
            achievement = Achievement(
                title=data.get('title'),
                type=data.get('type', ''),
                publish_time=publish_time,
                source_information=data.get('source_information', '')
            )
            db.session.add(achievement)
            db.session.flush()  # 获取 achievement_id
            
            # 关联到项目
            achievement_of_project = AchievementOfProject(
                achievement_id=achievement.achievement_id,
                project_id=data['project_id']
            )
            db.session.add(achievement_of_project)
            
            db.session.commit()
            return {'message': '成果上传成功', 'achievement_id': achievement.achievement_id}, 201
        except APIException:
            raise
        except Exception as e:
            logger.error(f"上传成果失败: {str(e)}", exc_info=True)
            db.session.rollback()
            raise APIException('上传成果失败，请稍后重试', 500)


class ProjectAchievementsResource(Resource):
    """项目成果列表"""
    @jwt_required()
    def get(self, project_id):
        """获取指定项目下的所有成果"""
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
                raise PermissionError('无权查看此项目的成果信息')
            
            # 查询项目关联的成果
            achievements = db.session.query(Achievement, AchievementOfProject).join(
                AchievementOfProject, Achievement.achievement_id == AchievementOfProject.achievement_id
            ).filter(
                AchievementOfProject.project_id == project_id
            ).order_by(Achievement.publish_time.desc()).all()
            
            return [{
                'achievement_id': a.Achievement.achievement_id,
                'title': a.Achievement.title,
                'type': a.Achievement.type or '',
                'publish_time': str(a.Achievement.publish_time) if a.Achievement.publish_time else None,
                'source_information': a.Achievement.source_information or '',
                'record_id': a.AchievementOfProject.record_id
            } for a in achievements]
        except APIException:
            raise
        except Exception as e:
            logger.error(f"获取项目成果列表失败: {str(e)}", exc_info=True)
            raise APIException('获取项目成果列表失败，请稍后重试', 500)
