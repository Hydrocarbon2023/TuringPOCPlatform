"""
孵化管理API资源
"""
import json
import logging
from datetime import datetime
from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_restful import Resource

from models import db, User, UserInTeam, Project, IncubationRecord, ProofOfConcept
from exceptions import ValidationError, PermissionError, APIException
from utils import get_current_user, create_default_milestones

logger = logging.getLogger(__name__)


class IncubationResourceAPI(Resource):
    """产业孵化管理"""
    @jwt_required()
    def get(self, project_id):
        """获取项目的孵化记录"""
        try:
            uid = get_jwt_identity()
            project = Project.query.get_or_404(project_id)
            
            # 权限检查：项目负责人、团队成员、管理员、秘书可见
            if str(project.principal_id) != str(uid):
                my_team_ids = db.session.query(UserInTeam.team_id).filter_by(user_id=uid).all()
                my_team_ids = [tid[0] for tid in my_team_ids]
                if project.team_id not in my_team_ids:
                    user = User.query.get(uid)
                    if not user or user.role not in ['管理员', '秘书']:
                        raise PermissionError('无权查看此项目的孵化信息')
            
            incubation = IncubationRecord.query.filter_by(project_id=project_id).first()
            if not incubation:
                return {'incubation': None}, 200
            
            milestones = []
            if incubation.milestones:
                try:
                    milestones = json.loads(incubation.milestones)
                except (json.JSONDecodeError, TypeError):
                    milestones = []
            
            return {
                'incubation': {
                    'incubation_id': incubation.incubation_id,
                    'project_id': incubation.project_id,
                    'start_time': str(incubation.start_time),
                    'planned_end_time': str(incubation.planned_end_time) if incubation.planned_end_time else None,
                    'actual_end_time': str(incubation.actual_end_time) if incubation.actual_end_time else None,
                    'status': incubation.status,
                    'progress': incubation.progress,
                    'incubation_plan': incubation.incubation_plan or '',
                    'milestones': milestones,
                    'resources': incubation.resources or '',
                    'challenges': incubation.challenges or '',
                    'achievements': incubation.achievements or '',
                    'update_time': str(incubation.update_time),
                }
            }
        except APIException:
            raise
        except Exception as e:
            logger.error(f"获取孵化信息失败: {str(e)}", exc_info=True)
            raise APIException('获取孵化信息失败，请稍后重试', 500)

    @jwt_required()
    def post(self, project_id):
        """创建或更新孵化计划"""
        try:
            uid = get_jwt_identity()
            project = Project.query.get_or_404(project_id)
            
            # 只有已通过、孵化中、概念验证中的项目才能创建/更新孵化计划
            if project.status not in ['已通过', '孵化中', '概念验证中']:
                raise ValidationError(f'项目状态为"{project.status}"，只有已通过复审的项目才能开始孵化')
            
            # 权限检查：只有项目负责人可以创建孵化计划
            if str(project.principal_id) != str(uid):
                raise PermissionError('只有项目负责人可以创建孵化计划')
            
            data = request.get_json()
            if not data:
                raise ValidationError('孵化计划数据不能为空')
            
            incubation = IncubationRecord.query.filter_by(project_id=project_id).first()
            
            # 如果是创建新记录，验证必填字段
            if not incubation and not data.get('incubation_plan'):
                raise ValidationError('孵化计划内容不能为空')
            
            if incubation:
                # 更新现有孵化记录
                if 'incubation_plan' in data:
                    incubation.incubation_plan = data['incubation_plan']
                if 'milestones' in data:
                    incubation.milestones = json.dumps(data['milestones'], ensure_ascii=False)
                if 'resources' in data:
                    incubation.resources = data['resources']
                if 'planned_end_time' in data and data['planned_end_time']:
                    try:
                        incubation.planned_end_time = datetime.strptime(data['planned_end_time'], '%Y-%m-%d')
                    except (ValueError, TypeError) as e:
                        logger.warning(f"日期格式解析失败: {data.get('planned_end_time')}, 错误: {str(e)}")
                        raise ValidationError('日期格式错误，应为 YYYY-MM-DD')
                if 'status' in data:
                    incubation.status = data['status']
                if 'progress' in data:
                    try:
                        progress = int(data['progress'])
                        if 0 <= progress <= 100:
                            incubation.progress = progress
                    except (ValueError, TypeError):
                        pass
                if 'challenges' in data:
                    incubation.challenges = data['challenges']
                if 'achievements' in data:
                    incubation.achievements = data['achievements']
                incubation.update_time = datetime.now()
            else:
                # 创建新孵化记录
                planned_end_time = None
                if data.get('planned_end_time'):
                    try:
                        planned_end_time = datetime.strptime(data['planned_end_time'], '%Y-%m-%d')
                    except (ValueError, TypeError) as e:
                        logger.warning(f"日期格式解析失败: {data.get('planned_end_time')}, 错误: {str(e)}")
                        raise ValidationError('日期格式错误，应为 YYYY-MM-DD')
                
                try:
                    progress = int(data.get('progress', 0))
                    if progress < 0 or progress > 100:
                        progress = 0
                except (ValueError, TypeError):
                    progress = 0
                
                incubation = IncubationRecord(
                    project_id=project_id,
                    incubation_plan=data.get('incubation_plan', ''),
                    milestones=json.dumps(data.get('milestones', []), ensure_ascii=False),
                    resources=data.get('resources', ''),
                    planned_end_time=planned_end_time,
                    status='进行中',
                    progress=progress,
                )
                db.session.add(incubation)
                # 如果项目状态是已通过，更新为孵化中
                if project.status == '已通过':
                    project.status = '孵化中'
                    # 自动创建默认里程碑
                    create_default_milestones(project_id)
            
            db.session.commit()
            return {'message': '孵化计划保存成功'}, 201
        except APIException:
            raise
        except ValueError as e:
            logger.error(f"日期格式错误: {str(e)}", exc_info=True)
            raise ValidationError('日期格式错误，应为 YYYY-MM-DD')
        except Exception as e:
            logger.error(f"保存孵化计划失败: {str(e)}", exc_info=True)
            db.session.rollback()
            raise APIException('保存孵化计划失败，请稍后重试', 500)


class ProofOfConceptResource(Resource):
    """概念验证管理"""
    @jwt_required()
    def get(self, project_id):
        """获取项目的概念验证记录列表"""
        try:
            uid = get_jwt_identity()
            project = Project.query.get_or_404(project_id)
            
            # 权限检查
            if str(project.principal_id) != str(uid):
                my_team_ids = db.session.query(UserInTeam.team_id).filter_by(user_id=uid).all()
                my_team_ids = [tid[0] for tid in my_team_ids]
                if project.team_id not in my_team_ids:
                    user = User.query.get(uid)
                    if user.role not in ['管理员', '秘书']:
                        raise PermissionError('无权查看此项目的概念验证信息')
            
            pocs = ProofOfConcept.query.filter_by(project_id=project_id).order_by(ProofOfConcept.create_time.desc()).all()
            
            return [{
                'poc_id': poc.poc_id,
                'project_id': poc.project_id,
                'incubation_id': poc.incubation_id,
                'title': poc.title,
                'description': poc.description,
                'verification_objective': poc.verification_objective,
                'verification_method': poc.verification_method,
                'verification_result': poc.verification_result,
                'status': poc.status,
                'start_time': str(poc.start_time),
                'end_time': str(poc.end_time) if poc.end_time else None,
                'evidence_files': json.loads(poc.evidence_files) if poc.evidence_files else [],
                'metrics': json.loads(poc.metrics) if poc.metrics else {},
                'conclusion': poc.conclusion,
                'create_time': str(poc.create_time),
            } for poc in pocs]
        except APIException:
            raise
        except Exception as e:
            logger.error(f"获取概念验证记录失败: {str(e)}", exc_info=True)
            raise APIException('获取概念验证记录失败，请稍后重试', 500)

    @jwt_required()
    def post(self, project_id):
        """创建概念验证记录"""
        try:
            uid = get_jwt_identity()
            project = Project.query.get_or_404(project_id)
            
            # 只有孵化中或概念验证中的项目才能创建概念验证
            if project.status not in ['孵化中', '概念验证中', '已通过']:
                raise ValidationError('项目必须处于孵化阶段才能进行概念验证')
            
            # 权限检查
            if str(project.principal_id) != str(uid):
                raise PermissionError('只有项目负责人可以创建概念验证记录')
            
            data = request.get_json()
            if not data or 'title' not in data:
                raise ValidationError('概念验证标题不能为空')
            
            poc = ProofOfConcept(
                project_id=project_id,
                incubation_id=data.get('incubation_id'),
                title=data['title'],
                description=data.get('description', ''),
                verification_objective=data.get('verification_objective', ''),
                verification_method=data.get('verification_method', ''),
                status='待开始',
            )
            
            db.session.add(poc)
            
            # 如果项目状态是已通过或孵化中，更新为概念验证中
            if project.status in ['已通过', '孵化中']:
                project.status = '概念验证中'
            
            db.session.commit()
            return {'message': '概念验证记录创建成功', 'poc_id': poc.poc_id}, 201
        except APIException:
            raise
        except Exception as e:
            logger.error(f"创建概念验证记录失败: {str(e)}", exc_info=True)
            db.session.rollback()
            raise APIException('创建概念验证记录失败，请稍后重试', 500)


class ProofOfConceptDetailResource(Resource):
    """概念验证详情管理"""
    @jwt_required()
    def put(self, poc_id):
        """更新概念验证记录"""
        try:
            uid = get_jwt_identity()
            poc = ProofOfConcept.query.get_or_404(poc_id)
            project = Project.query.get(poc.project_id)
            
            # 权限检查
            if str(project.principal_id) != str(uid):
                raise PermissionError('只有项目负责人可以更新概念验证记录')
            
            data = request.get_json()
            if not data:
                raise ValidationError('更新数据不能为空')
            
            if 'title' in data:
                poc.title = data['title']
            if 'description' in data:
                poc.description = data['description']
            if 'verification_objective' in data:
                poc.verification_objective = data['verification_objective']
            if 'verification_method' in data:
                poc.verification_method = data['verification_method']
            if 'verification_result' in data:
                poc.verification_result = data['verification_result']
            if 'status' in data:
                poc.status = data['status']
                if data['status'] in ['已完成', '已验证']:
                    poc.end_time = datetime.now()
            if 'evidence_files' in data:
                poc.evidence_files = json.dumps(data['evidence_files'], ensure_ascii=False)
            if 'metrics' in data:
                poc.metrics = json.dumps(data['metrics'], ensure_ascii=False)
            if 'conclusion' in data:
                poc.conclusion = data['conclusion']
            
            poc.update_time = datetime.now()
            db.session.commit()
            return {'message': '概念验证记录更新成功'}, 200
        except APIException:
            raise
        except Exception as e:
            logger.error(f"更新概念验证记录失败: {str(e)}", exc_info=True)
            db.session.rollback()
            raise APIException('更新概念验证记录失败，请稍后重试', 500)

    @jwt_required()
    def get(self, poc_id):
        """获取概念验证详情"""
        try:
            uid = get_jwt_identity()
            poc = ProofOfConcept.query.get_or_404(poc_id)
            project = Project.query.get(poc.project_id)
            
            # 权限检查
            if str(project.principal_id) != str(uid):
                my_team_ids = db.session.query(UserInTeam.team_id).filter_by(user_id=uid).all()
                my_team_ids = [tid[0] for tid in my_team_ids]
                if project.team_id not in my_team_ids:
                    user = User.query.get(uid)
                    if user.role not in ['管理员', '秘书']:
                        raise PermissionError('无权查看此概念验证记录')
            
            return {
                'poc_id': poc.poc_id,
                'project_id': poc.project_id,
                'incubation_id': poc.incubation_id,
                'title': poc.title,
                'description': poc.description,
                'verification_objective': poc.verification_objective,
                'verification_method': poc.verification_method,
                'verification_result': poc.verification_result,
                'status': poc.status,
                'start_time': str(poc.start_time),
                'end_time': str(poc.end_time) if poc.end_time else None,
                'evidence_files': json.loads(poc.evidence_files) if poc.evidence_files else [],
                'metrics': json.loads(poc.metrics) if poc.metrics else {},
                'conclusion': poc.conclusion,
                'create_time': str(poc.create_time),
                'update_time': str(poc.update_time),
            }
        except APIException:
            raise
        except Exception as e:
            logger.error(f"获取概念验证详情失败: {str(e)}", exc_info=True)
            raise APIException('获取概念验证详情失败，请稍后重试', 500)
