"""
秘书功能API资源
"""
import logging
from datetime import datetime
from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource

from models import db, Project, ReviewTask, AuditRecord
from exceptions import ValidationError, PermissionError, APIException
from utils import get_current_user

logger = logging.getLogger(__name__)


class ProjectAudit(Resource):
    """项目初审"""
    @jwt_required()
    def post(self, project_id):
        try:
            user = get_current_user()
            if user.role != '秘书':
                raise PermissionError('只有秘书有权进行初审')

            data = request.get_json()
            if not data or 'result' not in data:
                raise ValidationError('审核结果不能为空')
            
            project = Project.query.get_or_404(project_id)

            record = AuditRecord(
                project_id=project_id,
                auditor_id=user.user_id,
                audit_type='项目初审',
                result=data['result'],
                comment=data.get('comment')
            )
            db.session.add(record)

            if data['result'] == '通过':
                project.status = '复审中'
            else:
                project.status = '已取消'

            db.session.commit()
            return {'message': '初审完成'}, 201
        except APIException:
            raise
        except Exception as e:
            logger.error(f"项目初审失败: {str(e)}", exc_info=True)
            db.session.rollback()
            raise APIException('初审失败，请稍后重试', 500)


class TaskAssignment(Resource):
    """评审任务分配"""
    @jwt_required()
    def post(self, project_id):
        try:
            user = get_current_user()
            if user.role != '秘书':
                raise PermissionError('只有秘书有权分配评审人')

            data = request.get_json()
            if not data or 'reviewer_id' not in data:
                raise ValidationError('评审人ID不能为空')
            
            reviewer_id = data['reviewer_id']

            if ReviewTask.query.filter_by(project_id=project_id, reviewer_id=reviewer_id).first():
                raise ValidationError('该评审人已分配')

            deadline = None
            if data.get('deadline'):
                try:
                    deadline = datetime.strptime(data['deadline'], '%Y-%m-%d')
                except ValueError:
                    raise ValidationError('截止日期格式错误，应为 YYYY-MM-DD')

            task = ReviewTask(
                project_id=project_id,
                reviewer_id=reviewer_id,
                deadline=deadline,
                status='待确认'
            )
            db.session.add(task)
            db.session.commit()
            return {'message': '评审人分配成功'}, 201
        except APIException:
            raise
        except Exception as e:
            logger.error(f"分配评审人失败: {str(e)}", exc_info=True)
            db.session.rollback()
            raise APIException('分配评审人失败，请稍后重试', 500)
