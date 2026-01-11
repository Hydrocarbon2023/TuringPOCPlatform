"""
企业支持者API资源
"""
import logging
from datetime import datetime
from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_restful import Resource

from models import db, User, Project, SupportIntention
from exceptions import ValidationError, PermissionError, APIException
from utils import get_current_user

logger = logging.getLogger(__name__)


class SupporterProjectsResource(Resource):
    """支持者可浏览的孵化项目"""
    @jwt_required()
    def get(self):
        """获取正在孵化的项目列表（供支持者浏览）"""
        try:
            uid = get_jwt_identity()
            user = User.query.get(uid)
            
            if not user or user.role != '企业支持者':
                raise PermissionError('只有企业支持者可以浏览孵化项目')
            
            # 只返回状态为"孵化中"或"概念验证中"的项目
            projects = db.session.query(Project, User.real_name)\
                .join(User, Project.principal_id == User.user_id)\
                .filter(Project.status.in_(['孵化中', '概念验证中']))\
                .order_by(Project.submit_time.desc()).all()
            
            return [{
                'project_id': p.Project.project_id,
                'project_name': p.Project.project_name,
                'domain': p.Project.domain,
                'maturity_level': p.Project.maturity_level,
                'project_description': p.Project.project_description,
                'status': p.Project.status,
                'principal_name': p.real_name or '未知',
                'submit_time': str(p.Project.submit_time)
            } for p in projects]
        except APIException:
            raise
        except Exception as e:
            logger.error(f"获取孵化项目列表失败: {str(e)}", exc_info=True)
            raise APIException('获取孵化项目列表失败，请稍后重试', 500)


class SupportIntentionResource(Resource):
    """对接意向管理"""
    @jwt_required()
    def post(self):
        """提交对接意向"""
        try:
            uid = get_jwt_identity()
            user = User.query.get(uid)
            
            if not user or user.role != '企业支持者':
                raise PermissionError('只有企业支持者可以提交对接意向')
            
            data = request.get_json()
            if not data or not data.get('project_id') or not data.get('support_type'):
                raise ValidationError('项目ID和支持类型不能为空')
            
            project = Project.query.get_or_404(data['project_id'])
            
            # 检查项目状态
            if project.status not in ['孵化中', '概念验证中']:
                raise ValidationError('只能对接孵化中或概念验证中的项目')
            
            # 检查是否已提交过意向
            existing = SupportIntention.query.filter_by(
                project_id=data['project_id'],
                supporter_id=uid
            ).first()
            
            if existing:
                raise ValidationError('您已对该项目提交过对接意向')
            
            intention = SupportIntention(
                project_id=data['project_id'],
                supporter_id=uid,
                support_type=data['support_type'],
                message=data.get('message', ''),
                status='待处理'
            )
            db.session.add(intention)
            db.session.commit()
            
            return {'message': '对接意向提交成功', 'intention_id': intention.intention_id}, 201
        except APIException:
            raise
        except Exception as e:
            logger.error(f"提交对接意向失败: {str(e)}", exc_info=True)
            db.session.rollback()
            raise APIException('提交对接意向失败，请稍后重试', 500)


class ProjectIntentionsResource(Resource):
    """项目收到的对接意向"""
    @jwt_required()
    def get(self, project_id):
        """获取项目收到的所有对接意向（仅项目负责人）"""
        try:
            uid = get_jwt_identity()
            project = Project.query.get_or_404(project_id)
            
            # 权限检查：只有项目负责人可以查看
            if str(project.principal_id) != str(uid):
                raise PermissionError('只有项目负责人可以查看对接意向')
            
            intentions = db.session.query(SupportIntention, User.real_name, User.affiliation, User.email)\
                .join(User, SupportIntention.supporter_id == User.user_id)\
                .filter(SupportIntention.project_id == project_id)\
                .order_by(SupportIntention.create_time.desc()).all()
            
            return [{
                'intention_id': i.SupportIntention.intention_id,
                'project_id': i.SupportIntention.project_id,
                'supporter_id': i.SupportIntention.supporter_id,
                'support_type': i.SupportIntention.support_type,
                'message': i.SupportIntention.message,
                'status': i.SupportIntention.status,
                'create_time': str(i.SupportIntention.create_time),
                'update_time': str(i.SupportIntention.update_time),
                'supporter_name': i.real_name or '未知',
                'supporter_affiliation': i.affiliation or '',
                'supporter_email': i.email or ''
            } for i in intentions]
        except APIException:
            raise
        except Exception as e:
            logger.error(f"获取对接意向列表失败: {str(e)}", exc_info=True)
            raise APIException('获取对接意向列表失败，请稍后重试', 500)
    
    @jwt_required()
    def put(self, project_id):
        """更新对接意向状态（仅项目负责人）"""
        try:
            uid = get_jwt_identity()
            project = Project.query.get_or_404(project_id)
            
            if str(project.principal_id) != str(uid):
                raise PermissionError('只有项目负责人可以更新对接意向状态')
            
            data = request.get_json()
            if not data or not data.get('intention_id') or not data.get('status'):
                raise ValidationError('意向ID和状态不能为空')
            
            if data['status'] not in ['待处理', '已对接', '已婉拒']:
                raise ValidationError('状态值无效')
            
            intention = SupportIntention.query.filter_by(
                intention_id=data['intention_id'],
                project_id=project_id
            ).first_or_404()
            
            intention.status = data['status']
            intention.update_time = datetime.now()
            db.session.commit()
            
            return {'message': '对接意向状态更新成功'}
        except APIException:
            raise
        except Exception as e:
            logger.error(f"更新对接意向状态失败: {str(e)}", exc_info=True)
            db.session.rollback()
            raise APIException('更新对接意向状态失败，请稍后重试', 500)
