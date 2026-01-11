"""
项目管理API资源
"""
import logging
from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_restful import Resource
from sqlalchemy import or_, func

from models import db, User, Team, UserInTeam, Project, ReviewTask, ReviewOpinion
from exceptions import ValidationError, NotFoundError, PermissionError, APIException
from utils import get_current_user

logger = logging.getLogger(__name__)


class ProjectResource(Resource):
    """项目管理"""
    @jwt_required()
    def get(self, project_id=None):
        try:
            uid = get_jwt_identity()
            user = User.query.get(uid)

            if not user:
                raise NotFoundError('用户不存在')

            # 优化：直接获取团队ID列表，避免加载完整对象
            my_team_ids = db.session.query(UserInTeam.team_id).filter_by(user_id=uid).all()
            my_team_ids = [tid[0] for tid in my_team_ids]  # 解包元组

            # === 1. 获取详情 (单条查询) ===
            if project_id:
                result = db.session.query(Project, User.user_name) \
                    .outerjoin(User, Project.principal_id == User.user_id) \
                    .filter(Project.project_id == project_id).first()

                if not result:
                    raise NotFoundError('项目不存在')

                p, principal_name = result

                # 权限检查
                is_my_project = (str(p.principal_id) == str(uid))
                is_team_member = (p.team_id in my_team_ids)
                has_permission = (is_my_project or is_team_member or user.role in ['秘书', '管理员', '评审人'])

                if not has_permission:
                    raise PermissionError('无权查看此项目')

                # 【状态自动修复逻辑】
                if p.status == '复审中':
                    finished_reviews = ReviewTask.query.filter_by(project_id=p.project_id, status='已完成').count()
                    if finished_reviews >= 3:
                        result = db.session.query(
                            func.avg(ReviewOpinion.total_score).label('avg_score'),
                            func.count(ReviewOpinion.opinion_id).label('review_count')
                        ).join(ReviewTask, ReviewOpinion.task_id == ReviewTask.task_id) \
                         .filter(ReviewTask.project_id == p.project_id).first()

                        if result and result.review_count > 0:
                            avg_score = float(result.avg_score) if result.avg_score else 0
                            if avg_score > 60:
                                p.status = '已通过'
                            else:
                                p.status = '复审未通过'
                            try:
                                db.session.commit()
                            except Exception as e:
                                logger.error(f"保存项目状态失败: {str(e)}", exc_info=True)
                                db.session.rollback()

                # 优化：使用聚合查询一次性获取复审信息，避免N+1查询
                review_info = {}
                result = db.session.query(
                    func.avg(ReviewOpinion.total_score).label('avg_score'),
                    func.count(ReviewOpinion.opinion_id).label('review_count')
                ).join(ReviewTask, ReviewOpinion.task_id == ReviewTask.task_id) \
                 .filter(ReviewTask.project_id == p.project_id).first()

                if result and result.review_count > 0:
                    avg_score = float(result.avg_score) if result.avg_score else 0
                    review_info = {'avg_score': round(avg_score, 1), 'review_count': result.review_count}

                return {
                    'project_id': p.project_id,
                    'project_name': p.project_name,
                    'domain': p.domain,
                    'status': p.status,
                    'maturity_level': p.maturity_level,
                    'project_description': p.project_description,
                    'submit_time': str(p.submit_time),
                    'principal_name': principal_name or '未知',
                    'team_id': p.team_id,
                    'review_info': review_info
                }

            # === 2. 获取列表 (批量 JOIN 查询) ===
            query = db.session.query(Project, User.user_name) \
                .outerjoin(User, Project.principal_id == User.user_id)

            if user.role not in ['秘书', '管理员']:
                query = query.filter(
                    or_(
                        Project.team_id.in_(my_team_ids),
                        Project.principal_id == uid
                    )
                )

            results = query.order_by(Project.submit_time.desc()).all()

            return [{
                'project_id': p.project_id,
                'project_name': p.project_name,
                'domain': p.domain,
                'status': p.status,
                'principal_name': p_name or '未知'
            } for p, p_name in results]
        except APIException:
            raise
        except Exception as e:
            logger.error(f"获取项目列表失败: {str(e)}", exc_info=True)
            raise APIException('获取项目列表失败，请稍后重试', 500)

    @jwt_required()
    def post(self):
        """创建项目"""
        try:
            data = request.get_json()
            if not data or 'project_name' not in data:
                raise ValidationError('项目名称不能为空')
            
            uid = get_jwt_identity()
            user = User.query.get(uid)
            if not user:
                raise NotFoundError('用户不存在')

            tid = data.get('team_id')
            if not tid:
                user_teams = db.session.query(Team).join(UserInTeam).filter(UserInTeam.user_id == uid).all()
                if user_teams:
                    own_team = next((t for t in user_teams if str(t.leader_id) == str(uid)), None)
                    tid = own_team.team_id if own_team else user_teams[0].team_id
                else:
                    default_team = Team(
                        team_name=f"{user.user_name}的团队",
                        leader_id=uid,
                        domain='综合',
                        team_profile='个人自动创建的团队'
                    )
                    db.session.add(default_team)
                    db.session.flush()
                    db.session.add(UserInTeam(user_id=uid, team_id=default_team.team_id))
                    tid = default_team.team_id

            new_project = Project(
                project_name=data['project_name'],
                team_id=tid,
                principal_id=uid,
                domain=data.get('domain', '未分类'),
                maturity_level=data.get('maturity_level', '研发阶段'),
                project_description=data.get('project_description'),
                status='待初审'
            )
            db.session.add(new_project)
            db.session.commit()
            return {'message': '申报成功'}, 201
        except APIException:
            raise
        except Exception as e:
            logger.error(f"创建项目失败: {str(e)}", exc_info=True)
            db.session.rollback()
            raise APIException('创建项目失败，请稍后重试', 500)
