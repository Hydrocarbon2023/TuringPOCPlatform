"""
评审人功能API资源
"""
import logging
from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_restful import Resource
from sqlalchemy import func

from models import db, User, Project, ReviewTask, ReviewOpinion, Notification
from exceptions import ValidationError, NotFoundError, PermissionError, APIException
from utils import get_current_user

logger = logging.getLogger(__name__)


class ReviewerTasksResource(Resource):
    """评审任务列表"""
    @jwt_required()
    def get(self):
        try:
            uid = get_jwt_identity()
            tasks = db.session.query(ReviewTask, Project).join(Project, ReviewTask.project_id == Project.project_id) \
                .filter(ReviewTask.reviewer_id == uid).all()

            return [{
                'task_id': t.ReviewTask.task_id,
                'project_id': t.Project.project_id,
                'project_name': t.Project.project_name,
                'domain': t.Project.domain,
                'deadline': str(t.ReviewTask.deadline) if t.ReviewTask.deadline else '无',
                'status': t.ReviewTask.status
            } for t in tasks]
        except APIException:
            raise
        except Exception as e:
            logger.error(f"获取评审任务列表失败: {str(e)}", exc_info=True)
            raise APIException('获取评审任务列表失败，请稍后重试', 500)


class ReviewerIncubationProjectsResource(Resource):
    """评审人查看已进入孵化阶段的项目"""
    @jwt_required()
    def get(self):
        try:
            uid = get_jwt_identity()
            user = User.query.get(uid)
            if not user or user.role != '评审人':
                raise PermissionError('只有评审人可以查看孵化项目')
            
            reviewed_project_ids = db.session.query(ReviewTask.project_id)\
                .filter(ReviewTask.reviewer_id == uid)\
                .distinct().all()
            reviewed_project_ids = [pid[0] for pid in reviewed_project_ids]
            
            if not reviewed_project_ids:
                return []
            
            incubation_projects = db.session.query(Project, User.real_name)\
                .join(User, Project.principal_id == User.user_id)\
                .filter(
                    Project.project_id.in_(reviewed_project_ids),
                    Project.status.in_(['孵化中', '概念验证中', '孵化完成'])
                )\
                .order_by(Project.submit_time.desc()).all()
            
            return [{
                'project_id': p.Project.project_id,
                'project_name': p.Project.project_name,
                'domain': p.Project.domain,
                'maturity_level': p.Project.maturity_level,
                'status': p.Project.status,
                'principal_name': p.real_name or '未知',
                'submit_time': str(p.Project.submit_time)
            } for p in incubation_projects]
        except APIException:
            raise
        except Exception as e:
            logger.error(f"获取评审人孵化项目列表失败: {str(e)}", exc_info=True)
            raise APIException('获取孵化项目列表失败，请稍后重试', 500)


class ReviewerReview(Resource):
    """提交评审意见"""
    @jwt_required()
    def post(self, task_id):
        try:
            uid = get_jwt_identity()
            task = ReviewTask.query.get_or_404(task_id)
            if str(task.reviewer_id) != str(uid):
                raise PermissionError('无权操作此评审任务')

            data = request.get_json()
            if not data:
                raise ValidationError('评审数据不能为空')
            
            innovation = int(data.get('innovation', 0))
            feasibility = int(data.get('feasibility', 0))
            potentiality = int(data.get('potentiality', 0))
            teamwork = int(data.get('teamwork', 0))
            
            total = innovation + feasibility + potentiality + teamwork

            opinion = ReviewOpinion(
                task_id=task_id,
                innovation_score=innovation,
                feasibility_score=feasibility,
                potentiality_score=potentiality,
                teamwork_score=teamwork,
                total_score=total,
                comment=data.get('comment')
            )
            task.status = '已完成'
            db.session.add(opinion)
            db.session.commit()

            self.check_and_finalize(task.project_id)
            return {'message': '评审已提交'}, 201
        except APIException:
            raise
        except ValueError as e:
            logger.error(f"评审数据格式错误: {str(e)}", exc_info=True)
            raise ValidationError('评分数据格式错误')
        except Exception as e:
            logger.error(f"提交评审失败: {str(e)}", exc_info=True)
            db.session.rollback()
            raise APIException('提交评审失败，请稍后重试', 500)

    def check_and_finalize(self, project_id):
        """自动结算逻辑：满3人且均分>60通过"""
        finished_count = ReviewTask.query.filter_by(project_id=project_id, status='已完成').count()
        
        if finished_count >= 3:
            result = db.session.query(
                func.avg(ReviewOpinion.total_score).label('avg_score')
            ).join(ReviewTask, ReviewOpinion.task_id == ReviewTask.task_id) \
             .filter(ReviewTask.project_id == project_id).first()

            if result and result.avg_score is not None:
                avg_score = float(result.avg_score)
                project = Project.query.get(project_id)
                
                if not project:
                    logger.warning(f"项目 {project_id} 不存在")
                    return
                
                try:
                    if avg_score > 60:
                        project.status = '已通过'
                        msg = f"项目通过复审（均分{avg_score:.1f}），进入孵化阶段。"
                    else:
                        project.status = '复审未通过'
                        msg = f"项目复审未通过（均分{avg_score:.1f}）。"

                    notify = Notification(user_id=project.principal_id, title="复审结果", content=msg)
                    db.session.add(notify)
                    db.session.commit()
                except Exception as e:
                    logger.error(f"自动结算项目 {project_id} 失败: {str(e)}", exc_info=True)
                    db.session.rollback()


class NotificationResource(Resource):
    """通知管理"""
    @jwt_required()
    def get(self):
        try:
            uid = get_jwt_identity()
            notifs = Notification.query.filter_by(user_id=uid).order_by(Notification.create_time.desc()).all()
            return [{
                'id': n.notification_id,
                'title': n.title,
                'content': n.content,
                'create_time': str(n.create_time),
                'is_read': n.is_read
            } for n in notifs]
        except APIException:
            raise
        except Exception as e:
            logger.error(f"获取通知列表失败: {str(e)}", exc_info=True)
            raise APIException('获取通知列表失败，请稍后重试', 500)
