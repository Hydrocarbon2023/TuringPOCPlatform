"""
资源集市API资源
"""
import logging
from datetime import datetime
from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_restful import Resource

from models import db, User, Project, IncubationResource, ResourceApplication
from exceptions import ValidationError, PermissionError, APIException
from utils import get_current_user

logger = logging.getLogger(__name__)


class SupporterResourcesResource(Resource):
    """企业支持者发布资源"""
    @jwt_required()
    def post(self):
        """发布新资源（仅企业支持者）"""
        try:
            uid = get_jwt_identity()
            user = User.query.get(uid)
            if not user or user.role != '企业支持者':
                raise PermissionError('只有企业支持者可以发布资源')
            
            data = request.get_json()
            if not data or not data.get('title') or not data.get('resource_type'):
                raise ValidationError('资源标题和类型不能为空')
            
            resource = IncubationResource(
                provider_id=uid,
                title=data['title'],
                resource_type=data['resource_type'],
                description=data.get('description', ''),
                status='开放中'
            )
            db.session.add(resource)
            db.session.commit()
            
            return {'message': '资源发布成功', 'resource_id': resource.resource_id}, 201
        except APIException:
            raise
        except Exception as e:
            logger.error(f"发布资源失败: {str(e)}", exc_info=True)
            db.session.rollback()
            raise APIException('发布资源失败，请稍后重试', 500)
    
    @jwt_required()
    def get(self):
        """查看我发布的资源（仅企业支持者）"""
        try:
            uid = get_jwt_identity()
            user = User.query.get(uid)
            if not user or user.role != '企业支持者':
                raise PermissionError('只有企业支持者可以查看资源')
            
            resources = IncubationResource.query.filter_by(provider_id=uid)\
                .order_by(IncubationResource.create_time.desc()).all()
            
            return [{
                'resource_id': r.resource_id,
                'provider_id': r.provider_id,
                'title': r.title,
                'resource_type': r.resource_type,
                'description': r.description,
                'status': r.status,
                'create_time': str(r.create_time),
                'update_time': str(r.update_time),
            } for r in resources]
        except APIException:
            raise
        except Exception as e:
            logger.error(f"获取资源列表失败: {str(e)}", exc_info=True)
            raise APIException('获取资源列表失败，请稍后重试', 500)


class ResourceApplicationsResource(Resource):
    """查看资源收到的申请"""
    @jwt_required()
    def get(self, resource_id):
        """查看某资源收到的所有申请（仅资源发布者）"""
        try:
            uid = get_jwt_identity()
            resource = IncubationResource.query.get_or_404(resource_id)
            
            # 权限检查：只有资源发布者可以查看申请
            if str(resource.provider_id) != str(uid):
                raise PermissionError('只有资源发布者可以查看申请')
            
            applications = db.session.query(
                ResourceApplication, 
                Project.project_name,
                User.real_name,
                User.affiliation
            ).join(Project, ResourceApplication.project_id == Project.project_id)\
            .join(User, ResourceApplication.applicant_id == User.user_id)\
            .filter(ResourceApplication.resource_id == resource_id)\
            .order_by(ResourceApplication.create_time.desc()).all()
            
            return [{
                'application_id': a.ResourceApplication.application_id,
                'resource_id': a.ResourceApplication.resource_id,
                'project_id': a.ResourceApplication.project_id,
                'applicant_id': a.ResourceApplication.applicant_id,
                'status': a.ResourceApplication.status,
                'message': a.ResourceApplication.message,
                'reply': a.ResourceApplication.reply,
                'create_time': str(a.ResourceApplication.create_time),
                'update_time': str(a.ResourceApplication.update_time),
                'project_name': a.project_name,
                'applicant_name': a.real_name or '未知',
                'applicant_affiliation': a.affiliation or '',
            } for a in applications]
        except APIException:
            raise
        except Exception as e:
            logger.error(f"获取申请列表失败: {str(e)}", exc_info=True)
            raise APIException('获取申请列表失败，请稍后重试', 500)


class ApplicationHandleResource(Resource):
    """处理申请（同意/拒绝/标记为已达成）"""
    @jwt_required()
    def put(self, application_id):
        """处理申请（仅资源发布者）"""
        try:
            uid = get_jwt_identity()
            application = ResourceApplication.query.get_or_404(application_id)
            resource = IncubationResource.query.get_or_404(application.resource_id)
            
            # 权限检查：只有资源发布者可以处理申请
            if str(resource.provider_id) != str(uid):
                raise PermissionError('只有资源发布者可以处理申请')
            
            data = request.get_json()
            if not data or not data.get('status'):
                raise ValidationError('状态不能为空')
            
            if data['status'] not in ['待处理', '对接中', '已达成', '已拒绝']:
                raise ValidationError('无效的状态值')
            
            application.status = data['status']
            if data.get('reply'):
                application.reply = data['reply']
            application.update_time = datetime.now()
            db.session.commit()
            
            return {'message': '申请处理成功'}
        except APIException:
            raise
        except Exception as e:
            logger.error(f"处理申请失败: {str(e)}", exc_info=True)
            db.session.rollback()
            raise APIException('处理申请失败，请稍后重试', 500)


class PublicResourcesResource(Resource):
    """浏览开放中的资源（项目负责人）"""
    @jwt_required()
    def get(self):
        """浏览所有开放中的资源（支持按类型筛选）"""
        try:
            uid = get_jwt_identity()
            resource_type = request.args.get('resource_type')
            
            resources = db.session.query(
                IncubationResource,
                User.real_name,
                User.affiliation
            ).join(User, IncubationResource.provider_id == User.user_id)\
            .filter(IncubationResource.status == '开放中')\
            .order_by(IncubationResource.create_time.desc()).all()
            
            if resource_type:
                resources = [r for r in resources if r.IncubationResource.resource_type == resource_type]
            
            return [{
                'resource_id': r.IncubationResource.resource_id,
                'provider_id': r.IncubationResource.provider_id,
                'title': r.IncubationResource.title,
                'resource_type': r.IncubationResource.resource_type,
                'description': r.IncubationResource.description,
                'status': r.IncubationResource.status,
                'create_time': str(r.IncubationResource.create_time),
                'provider_name': r.real_name or '未知',
                'provider_affiliation': r.affiliation or '',
            } for r in resources]
        except APIException:
            raise
        except Exception as e:
            logger.error(f"获取资源列表失败: {str(e)}", exc_info=True)
            raise APIException('获取资源列表失败，请稍后重试', 500)


class ResourceApplyResource(Resource):
    """申请资源对接"""
    @jwt_required()
    def post(self, resource_id):
        """对某个资源提交申请（项目负责人）"""
        try:
            uid = get_jwt_identity()
            resource = IncubationResource.query.get_or_404(resource_id)
            
            if resource.status != '开放中':
                raise ValidationError('该资源已关闭')
            
            data = request.get_json()
            if not data or not data.get('project_id'):
                raise ValidationError('项目ID不能为空')
            
            project = Project.query.get_or_404(data['project_id'])
            
            # 权限检查：只有项目负责人可以申请
            if str(project.principal_id) != str(uid):
                raise PermissionError('只有项目负责人可以申请资源')
            
            # 检查是否已申请过
            existing = ResourceApplication.query.filter_by(
                resource_id=resource_id,
                project_id=data['project_id']
            ).first()
            
            if existing:
                raise ValidationError('您已对该资源提交过申请')
            
            application = ResourceApplication(
                resource_id=resource_id,
                project_id=data['project_id'],
                applicant_id=uid,
                status='待处理',
                message=data.get('message', '')
            )
            db.session.add(application)
            db.session.commit()
            
            return {'message': '申请提交成功', 'application_id': application.application_id}, 201
        except APIException:
            raise
        except Exception as e:
            logger.error(f"提交申请失败: {str(e)}", exc_info=True)
            db.session.rollback()
            raise APIException('提交申请失败，请稍后重试', 500)


class MyResourceApplicationsResource(Resource):
    """查看我的申请进度"""
    @jwt_required()
    def get(self):
        """查看我的申请进度（项目负责人）"""
        try:
            uid = get_jwt_identity()
            
            applications = db.session.query(
                ResourceApplication,
                IncubationResource.title,
                IncubationResource.resource_type,
                Project.project_name,
                User.real_name,
                User.affiliation
            ).join(IncubationResource, ResourceApplication.resource_id == IncubationResource.resource_id)\
            .join(Project, ResourceApplication.project_id == Project.project_id)\
            .join(User, IncubationResource.provider_id == User.user_id)\
            .filter(ResourceApplication.applicant_id == uid)\
            .order_by(ResourceApplication.create_time.desc()).all()
            
            return [{
                'application_id': a.ResourceApplication.application_id,
                'resource_id': a.ResourceApplication.resource_id,
                'project_id': a.ResourceApplication.project_id,
                'status': a.ResourceApplication.status,
                'message': a.ResourceApplication.message,
                'reply': a.ResourceApplication.reply,
                'create_time': str(a.ResourceApplication.create_time),
                'update_time': str(a.ResourceApplication.update_time),
                'resource_title': a.title,
                'resource_type': a.resource_type,
                'project_name': a.project_name,
                'provider_name': a.real_name or '未知',
                'provider_affiliation': a.affiliation or '',
            } for a in applications]
        except APIException:
            raise
        except Exception as e:
            logger.error(f"获取申请列表失败: {str(e)}", exc_info=True)
            raise APIException('获取申请列表失败，请稍后重试', 500)
