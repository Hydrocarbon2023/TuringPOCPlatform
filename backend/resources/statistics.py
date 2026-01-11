"""
数据统计API资源
"""
import logging
from datetime import datetime, timedelta
from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_restful import Resource
from sqlalchemy import func, text

from models import (
    db, User, Project, FundRecord, Expenditure, IncubationRecord,
    ReviewTask, ReviewOpinion, Milestone, IncubationResource,
    ResourceApplication, SupportIntention
)
from exceptions import PermissionError, APIException
from utils import get_current_user

logger = logging.getLogger(__name__)


class StatisticsResource(Resource):
    """数据统计API（管理员/秘书可见）"""
    @jwt_required()
    def get(self):
        """获取全局统计数据"""
        try:
            uid = get_jwt_identity()
            user = User.query.get(uid)
            if not user or user.role not in ['管理员', '秘书']:
                raise PermissionError('只有管理员或秘书可以查看统计数据')
            
            # 项目状态统计
            project_status_stats = db.session.query(
                Project.status,
                func.count(Project.project_id).label('count')
            ).group_by(Project.status).all()
            
            # 项目领域统计
            project_domain_stats = db.session.query(
                Project.domain,
                func.count(Project.project_id).label('count')
            ).filter(Project.domain.isnot(None)).group_by(Project.domain).all()
            
            # 用户角色统计
            user_role_stats = db.session.query(
                User.role,
                func.count(User.user_id).label('count')
            ).group_by(User.role).all()
            
            # 项目成熟度统计
            project_maturity_stats = db.session.query(
                Project.maturity_level,
                func.count(Project.project_id).label('count')
            ).group_by(Project.maturity_level).all()
            
            # 项目提交时间趋势（按月统计，最近12个月）
            twelve_months_ago = datetime.now() - timedelta(days=365)
            project_trend = db.session.query(
                func.date_format(Project.submit_time, text("'%Y-%m'")).label('month'),
                func.count(Project.project_id).label('count')
            ).filter(Project.submit_time >= twelve_months_ago)\
            .group_by(func.date_format(Project.submit_time, text("'%Y-%m'")))\
            .order_by(text('month')).all()
            
            # 经费统计
            fund_stats = db.session.query(
                func.sum(FundRecord.amount).label('total_allocated'),
                func.sum(Expenditure.amount).label('total_expended')
            ).first()
            
            # 孵化项目统计
            incubation_stats = db.session.query(
                func.count(IncubationRecord.incubation_id).label('total'),
                func.avg(IncubationRecord.progress).label('avg_progress')
            ).first()
            
            # 评审统计
            review_stats = db.session.query(
                ReviewTask.status,
                func.count(ReviewTask.task_id).label('count')
            ).group_by(ReviewTask.status).all()
            
            return {
                'project_status': [{'status': s[0], 'count': s[1]} for s in project_status_stats],
                'project_domain': [{'domain': d[0] or '未分类', 'count': d[1]} for d in project_domain_stats],
                'user_role': [{'role': r[0], 'count': r[1]} for r in user_role_stats],
                'project_maturity': [{'level': m[0], 'count': m[1]} for m in project_maturity_stats],
                'project_trend': [{'month': t[0], 'count': t[1]} for t in project_trend],
                'fund': {
                    'total_allocated': float(fund_stats[0] or 0),
                    'total_expended': float(fund_stats[1] or 0),
                },
                'incubation': {
                    'total': incubation_stats[0] or 0,
                    'avg_progress': float(incubation_stats[1] or 0),
                },
                'review_status': [{'status': r[0], 'count': r[1]} for r in review_stats],
            }
        except APIException:
            raise
        except Exception as e:
            logger.error(f"获取统计数据失败: {str(e)}", exc_info=True)
            raise APIException('获取统计数据失败，请稍后重试', 500)


class UserStatisticsResource(Resource):
    """用户个人统计数据（项目负责人）"""
    @jwt_required()
    def get(self):
        """获取当前用户的项目统计数据"""
        try:
            uid = get_jwt_identity()
            
            # 我的项目状态统计
            my_projects = Project.query.filter_by(principal_id=uid).all()
            project_status_stats = {}
            for project in my_projects:
                status = project.status
                project_status_stats[status] = project_status_stats.get(status, 0) + 1
            
            # 我的项目领域统计
            project_domain_stats = {}
            for project in my_projects:
                domain = project.domain or '未分类'
                project_domain_stats[domain] = project_domain_stats.get(domain, 0) + 1
            
            # 我的经费统计
            my_fund_stats = db.session.query(
                func.sum(FundRecord.amount).label('total_allocated'),
                func.sum(Expenditure.amount).label('total_expended')
            ).join(Project, FundRecord.project_id == Project.project_id)\
            .filter(Project.principal_id == uid).first()
            
            # 我的里程碑统计
            my_project_ids = [p.project_id for p in my_projects]
            milestone_stats = db.session.query(
                Milestone.status,
                func.count(Milestone.milestone_id).label('count')
            ).filter(Milestone.project_id.in_(my_project_ids)).group_by(Milestone.status).all() if my_project_ids else []
            
            return {
                'project_status': [{'status': k, 'count': v} for k, v in project_status_stats.items()],
                'project_domain': [{'domain': k, 'count': v} for k, v in project_domain_stats.items()],
                'fund': {
                    'total_allocated': float(my_fund_stats[0] or 0),
                    'total_expended': float(my_fund_stats[1] or 0),
                },
                'milestone_status': [{'status': m[0], 'count': m[1]} for m in milestone_stats],
            }
        except APIException:
            raise
        except Exception as e:
            logger.error(f"获取用户统计数据失败: {str(e)}", exc_info=True)
            raise APIException('获取统计数据失败，请稍后重试', 500)


class ReviewerStatisticsResource(Resource):
    """评审人统计数据"""
    @jwt_required()
    def get(self):
        """获取当前评审人的评审统计数据"""
        try:
            uid = get_jwt_identity()
            user = User.query.get(uid)
            if not user or user.role != '评审人':
                raise PermissionError('只有评审人可以查看评审统计数据')
            
            # 我的评审任务状态统计
            my_tasks = ReviewTask.query.filter_by(reviewer_id=uid).all()
            task_status_stats = {}
            for task in my_tasks:
                status = task.status
                task_status_stats[status] = task_status_stats.get(status, 0) + 1
            
            # 我的评审评分统计（如果有评分数据）
            my_opinions = db.session.query(ReviewOpinion, ReviewTask)\
                .join(ReviewTask, ReviewOpinion.task_id == ReviewTask.task_id)\
                .filter(ReviewTask.reviewer_id == uid).all()
            
            score_stats = {
                'avg_innovation': 0,
                'avg_feasibility': 0,
                'avg_teamwork': 0,
                'avg_potentiality': 0,
            }
            
            if my_opinions:
                total = len(my_opinions)
                score_stats = {
                    'avg_innovation': sum(o[0].innovation_score for o in my_opinions) / total,
                    'avg_feasibility': sum(o[0].feasibility_score for o in my_opinions) / total,
                    'avg_teamwork': sum(o[0].teamwork_score for o in my_opinions) / total,
                    'avg_potentiality': sum(o[0].potentiality_score for o in my_opinions) / total,
                }
            
            # 我评审的项目领域统计
            reviewed_project_ids = [t.project_id for t in my_tasks]
            reviewed_domains = db.session.query(Project.domain)\
                .filter(Project.project_id.in_(reviewed_project_ids)).all() if reviewed_project_ids else []
            domain_stats = {}
            for domain_tuple in reviewed_domains:
                domain = domain_tuple[0] or '未分类'
                domain_stats[domain] = domain_stats.get(domain, 0) + 1
            
            return {
                'task_status': [{'status': k, 'count': v} for k, v in task_status_stats.items()],
                'score_stats': score_stats,
                'reviewed_domains': [{'domain': k, 'count': v} for k, v in domain_stats.items()],
                'total_reviews': len(my_opinions),
            }
        except APIException:
            raise
        except Exception as e:
            logger.error(f"获取评审统计数据失败: {str(e)}", exc_info=True)
            raise APIException('获取统计数据失败，请稍后重试', 500)


class SupporterStatisticsResource(Resource):
    """企业支持者统计数据"""
    @jwt_required()
    def get(self):
        """获取当前企业支持者的资源统计数据"""
        try:
            uid = get_jwt_identity()
            user = User.query.get(uid)
            if not user or user.role != '企业支持者':
                raise PermissionError('只有企业支持者可以查看资源统计数据')
            
            # 我发布的资源统计
            my_resources = IncubationResource.query.filter_by(provider_id=uid).all()
            resource_type_stats = {}
            resource_status_stats = {}
            for resource in my_resources:
                rtype = resource.resource_type
                resource_type_stats[rtype] = resource_type_stats.get(rtype, 0) + 1
                status = resource.status
                resource_status_stats[status] = resource_status_stats.get(status, 0) + 1
            
            # 我的资源申请统计
            my_resource_ids = [r.resource_id for r in my_resources]
            application_stats = db.session.query(
                ResourceApplication.status,
                func.count(ResourceApplication.application_id).label('count')
            ).filter(ResourceApplication.resource_id.in_(my_resource_ids))\
            .group_by(ResourceApplication.status).all() if my_resource_ids else []
            
            # 对接意向统计
            intention_stats = db.session.query(
                SupportIntention.status,
                func.count(SupportIntention.intention_id).label('count')
            ).filter(SupportIntention.supporter_id == uid)\
            .group_by(SupportIntention.status).all()
            
            return {
                'resource_type': [{'type': k, 'count': v} for k, v in resource_type_stats.items()],
                'resource_status': [{'status': k, 'count': v} for k, v in resource_status_stats.items()],
                'application_status': [{'status': a[0], 'count': a[1]} for a in application_stats],
                'intention_status': [{'status': i[0], 'count': i[1]} for i in intention_stats],
                'total_resources': len(my_resources),
            }
        except APIException:
            raise
        except Exception as e:
            logger.error(f"获取企业支持者统计数据失败: {str(e)}", exc_info=True)
            raise APIException('获取统计数据失败，请稍后重试', 500)
