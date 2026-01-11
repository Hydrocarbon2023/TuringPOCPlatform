import bcrypt
import json
import logging
from datetime import datetime

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import (JWTManager, create_access_token,
                                get_jwt_identity, jwt_required)
from flask_restful import Api, Resource
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_, func
from sqlalchemy.orm import joinedload
from flask_migrate import Migrate

from config import Config
from models import (db, User, Team, UserInTeam, Project, FundRecord,
                    Expenditure, ReviewTask, ReviewOpinion, AuditRecord,
                    Achievement, AchievementOfProject, Notification,
                    IncubationRecord, ProofOfConcept, Milestone,
                    IncubationComment, SupportIntention, IncubationResource,
                    ResourceApplication)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)
migrate = Migrate(app, db)
jwt = JWTManager(app)
CORS(app)
api = Api(app)


# --- 自定义异常类 ---
class APIException(Exception):
    """API异常基类"""
    def __init__(self, message, status_code=400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class ValidationError(APIException):
    """数据验证错误"""
    def __init__(self, message):
        super().__init__(message, 400)


class NotFoundError(APIException):
    """资源未找到错误"""
    def __init__(self, message="资源不存在"):
        super().__init__(message, 404)


class PermissionError(APIException):
    """权限错误"""
    def __init__(self, message="权限不足"):
        super().__init__(message, 403)


# --- 全局错误处理器 ---
@app.errorhandler(APIException)
def handle_api_exception(e):
    """处理自定义API异常"""
    logger.warning(f"API异常: {e.message} (状态码: {e.status_code})")
    return jsonify({'message': e.message}), e.status_code


@app.errorhandler(404)
def handle_not_found(e):
    """处理404错误"""
    return jsonify({'message': '资源不存在'}), 404


@app.errorhandler(500)
def handle_internal_error(e):
    """处理500错误"""
    logger.error(f"服务器内部错误: {str(e)}", exc_info=True)
    return jsonify({'message': '服务器内部错误，请稍后重试'}), 500


@app.errorhandler(Exception)
def handle_general_exception(e):
    """处理其他未捕获的异常"""
    logger.error(f"未处理的异常: {str(e)}", exc_info=True)
    return jsonify({'message': '服务器错误，请稍后重试'}), 500


# --- 辅助函数 ---
def get_current_user():
    """获取当前登录用户"""
    uid = get_jwt_identity()
    user = User.query.get(uid)
    if not user:
        raise NotFoundError("用户不存在")
    return user


def create_default_milestones(project_id):
    """为项目创建默认里程碑"""
    try:
        # 检查是否已存在里程碑，避免重复创建
        existing_count = Milestone.query.filter_by(project_id=project_id).count()
        if existing_count > 0:
            return  # 已存在里程碑，不重复创建
        
        # 计算默认日期（基于当前时间和孵化周期）
        from datetime import timedelta
        base_date = datetime.now()
        
        default_milestones = [
            {
                'title': '原型验证',
                'due_date': base_date + timedelta(days=90),
                'status': '未开始',
                'deliverable': '完成原型开发，提交原型验证报告'
            },
            {
                'title': '中期检查',
                'due_date': base_date + timedelta(days=180),
                'status': '未开始',
                'deliverable': '完成中期进度报告，提交关键成果文档'
            },
            {
                'title': '结项验收',
                'due_date': base_date + timedelta(days=365),
                'status': '未开始',
                'deliverable': '完成所有交付物，提交结项报告和最终成果'
            }
        ]
        
        for milestone_data in default_milestones:
            milestone = Milestone(
                project_id=project_id,
                title=milestone_data['title'],
                due_date=milestone_data['due_date'],
                status=milestone_data['status'],
                deliverable=milestone_data['deliverable']
            )
            db.session.add(milestone)
        
        logger.info(f"为项目 {project_id} 创建了 {len(default_milestones)} 个默认里程碑")
    except Exception as e:
        logger.error(f"创建默认里程碑失败: {str(e)}", exc_info=True)
        # 不影响主流程，仅记录错误


# --- 1. 认证与用户管理 ---

class Login(Resource):
    def post(self):
        try:
            data = request.get_json()
            if not data or 'user_name' not in data or 'password' not in data:
                raise ValidationError('用户名和密码不能为空')
            
            user = User.query.filter_by(user_name=data['user_name']).first()
            if user and user.check_password(data['password']):
                access_token = create_access_token(identity=str(user.user_id))
                return {
                    'token': access_token,
                    'role': user.role,
                    'user_name': user.user_name,
                    'real_name': user.real_name,
                    'user_id': user.user_id
                }
            return {'message': '用户名或密码错误'}, 401
        except APIException:
            raise
        except Exception as e:
            logger.error(f"登录失败: {str(e)}", exc_info=True)
            raise APIException('登录失败，请稍后重试', 500)


class Register(Resource):
    def post(self):
        try:
            data = request.get_json()
            if not data or 'user_name' not in data or 'password' not in data:
                raise ValidationError('用户名和密码不能为空')
            
            if User.query.filter_by(user_name=data['user_name']).first():
                raise ValidationError('用户名已存在')
            
            # 允许注册时选择角色
            role = data.get('role', '项目参与者')
            valid_roles = ['项目参与者', '评审人', '秘书', '企业支持者']
            if role not in valid_roles:
                role = '项目参与者'  # 默认角色
            
            new_user = User(
                user_name=data['user_name'],
                real_name=data.get('real_name'),
                role=role,
                affiliation=data.get('affiliation'),
                email=data.get('email')
            )
            new_user.set_password(data['password'])
            db.session.add(new_user)
            db.session.commit()
            return {'message': '注册成功'}, 201
        except APIException:
            raise
        except Exception as e:
            logger.error(f"注册失败: {str(e)}", exc_info=True)
            db.session.rollback()
            raise APIException('注册失败，请稍后重试', 500)


class AdminUserResource(Resource):
    @jwt_required()
    def post(self):
        try:
            current_user = get_current_user()
            if current_user.role != '管理员':
                raise PermissionError('只有管理员可以创建用户')

            data = request.get_json()
            if not data or 'user_name' not in data or 'password' not in data:
                raise ValidationError('用户名和密码不能为空')

            if User.query.filter_by(user_name=data['user_name']).first():
                raise ValidationError('用户名已存在')

            new_user = User(
                user_name=data['user_name'],
                real_name=data['real_name'],
                role=data['role'],
                affiliation=data.get('affiliation'),
                email=data.get('email')
            )
            new_user.set_password(data['password'])
            db.session.add(new_user)
            db.session.commit()
            return {'message': f'已创建用户: {data["real_name"]}'}, 201
        except APIException:
            raise
        except Exception as e:
            logger.error(f"创建用户失败: {str(e)}", exc_info=True)
            db.session.rollback()
            raise APIException('创建用户失败，请稍后重试', 500)

    @jwt_required()
    def get(self):
        users = User.query.all()
        return [{
            'user_id': u.user_id,
            'user_name': u.user_name,
            'real_name': u.real_name,
            'role': u.role,
            'affiliation': u.affiliation
        } for u in users]


# --- 2. 团队管理 ---

class TeamResource(Resource):
    @jwt_required()
    def get(self):
        """获取所有团队列表 (管理员/秘书可见)"""
        # 优化：使用JOIN一次性获取leader信息，使用聚合查询获取成员数量
        # 避免N+1查询问题
        results = db.session.query(
            Team,
            User.user_name.label('leader_name'),
            func.count(UserInTeam.user_id).label('member_count')
        ).outerjoin(User, Team.leader_id == User.user_id) \
         .outerjoin(UserInTeam, Team.team_id == UserInTeam.team_id) \
         .group_by(Team.team_id, User.user_name) \
         .all()
        
        return [{
            'team_id': t.team_id,
            'team_name': t.team_name,
            'leader_id': t.leader_id,
            'leader_name': leader_name or '未知',
            'domain': t.domain,
            'member_count': member_count or 0
        } for t, leader_name, member_count in results]

    @jwt_required()
    def post(self):
        data = request.get_json()
        uid = get_jwt_identity()

        new_team = Team(
            team_name=data['team_name'],
            leader_id=uid,
            domain=data.get('domain', '综合'),
            team_profile=data.get('team_profile')
        )
        db.session.add(new_team)
        db.session.flush()

        # 队长自动入队
        join = UserInTeam(user_id=uid, team_id=new_team.team_id)
        db.session.add(join)

        db.session.commit()
        return {'message': '团队创建成功', 'team_id': new_team.team_id}, 201


class MyTeamsResource(Resource):
    """获取当前用户所属的团队信息"""

    @jwt_required()
    def get(self):
        uid = get_jwt_identity()
        # 优化：使用JOIN一次性获取leader信息，避免N+1查询
        results = db.session.query(Team, User.user_name.label('leader_name')) \
            .join(UserInTeam, Team.team_id == UserInTeam.team_id) \
            .outerjoin(User, Team.leader_id == User.user_id) \
            .filter(UserInTeam.user_id == uid).all()
        
        return [{
            'team_id': t.team_id,
            'team_name': t.team_name,
            'domain': t.domain,
            'role': '队长' if str(t.leader_id) == str(uid) else '成员',
            'leader_name': leader_name or '未知'
        } for t, leader_name in results]


class TeamMembersResource(Resource):
    @jwt_required()
    def post(self, team_id):
        try:
            current_uid = get_jwt_identity()
            team = Team.query.get_or_404(team_id)
            if str(team.leader_id) != str(current_uid):
                raise PermissionError('只有队长可以邀请成员')

            data = request.get_json()
            if not data or 'user_name' not in data:
                raise ValidationError('用户名不能为空')
            
            target_username = data.get('user_name')
            target_user = User.query.filter_by(user_name=target_username).first()

            if not target_user:
                raise NotFoundError('用户不存在')

            exists = UserInTeam.query.filter_by(user_id=target_user.user_id, team_id=team_id).first()
            if exists:
                raise ValidationError('该用户已在团队中')

            new_member = UserInTeam(user_id=target_user.user_id, team_id=team_id)
            db.session.add(new_member)
            db.session.commit()
            return {'message': f'已邀请 {target_user.real_name} 加入团队'}, 201
        except APIException:
            raise
        except Exception as e:
            logger.error(f"邀请团队成员失败: {str(e)}", exc_info=True)
            db.session.rollback()
            raise APIException('邀请成员失败，请稍后重试', 500)

    @jwt_required()
    def get(self, team_id):
        # 优化：一次性查询team和members，避免额外查询
        team = Team.query.get_or_404(team_id)
        members = db.session.query(User).join(UserInTeam).filter(UserInTeam.team_id == team_id).all()
        return [{
            'user_id': u.user_id,
            'user_name': u.user_name,
            'role': '队长' if u.user_id == team.leader_id else '成员'
        } for u in members]


# --- 3. 项目管理 ---

class ProjectResource(Resource):
    @jwt_required()
    def get(self, project_id=None):
        uid = get_jwt_identity()
        user = User.query.get(uid)

        if not user:
            raise NotFoundError('用户不存在')

        # 优化：直接获取团队ID列表，避免加载完整对象
        my_team_ids = db.session.query(UserInTeam.team_id).filter_by(user_id=uid).all()
        my_team_ids = [tid[0] for tid in my_team_ids]  # 解包元组

        # === 1. 获取详情 (单条查询) ===
        if project_id:
            # JOIN User 获取 user_name
            # 这里使用了外连接 (outerjoin)，即使没有负责人也能查出项目
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
                    # 优化：使用聚合查询一次性计算平均分，避免加载所有opinions
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
                            db.session.commit()  # 尝试保存状态
                        except Exception as e:
                            logger.error(f"保存项目状态失败: {str(e)}", exc_info=True)
                            db.session.rollback()  # 防止出错影响后续

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

    @jwt_required()
    def post(self):
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


# --- 4. 秘书功能 ---

class ProjectAudit(Resource):
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


# --- 5. 评审人评审 ---

class ReviewerTasksResource(Resource):
    @jwt_required()
    def get(self):
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


class ReviewerIncubationProjectsResource(Resource):
    """评审人查看已进入孵化阶段的项目"""
    @jwt_required()
    def get(self):
        """获取评审人评审过的、已进入孵化阶段的项目列表"""
        try:
            uid = get_jwt_identity()
            user = User.query.get(uid)
            if not user or user.role != '评审人':
                raise PermissionError('只有评审人可以查看孵化项目')
            
            # 获取评审人评审过的项目ID列表
            reviewed_project_ids = db.session.query(ReviewTask.project_id)\
                .filter(ReviewTask.reviewer_id == uid)\
                .distinct().all()
            reviewed_project_ids = [pid[0] for pid in reviewed_project_ids]
            
            if not reviewed_project_ids:
                return []
            
            # 获取这些项目中已进入孵化阶段的项目
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
            
            # 验证评分字段
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
        # 优化：使用聚合查询一次性获取完成的任务数和平均分
        finished_count = ReviewTask.query.filter_by(project_id=project_id, status='已完成').count()
        
        if finished_count >= 3:
            # 优化：使用聚合查询计算平均分，避免加载所有opinions
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
    @jwt_required()
    def get(self):
        uid = get_jwt_identity()
        # 获取当前用户的未读或所有通知
        notifs = Notification.query.filter_by(user_id=uid).order_by(Notification.create_time.desc()).all()
        return [{
            'id': n.notification_id,
            'title': n.title,
            'content': n.content,
            'create_time': str(n.create_time),
            'is_read': n.is_read
        } for n in notifs]


# --- 6. 产业孵化与概念验证 ---

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
                        pass  # 忽略无效的进度值
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
                my_team_ids = [r.team_id for r in UserInTeam.query.filter_by(user_id=uid).all()]
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
                my_team_ids = [r.team_id for r in UserInTeam.query.filter_by(user_id=uid).all()]
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


# --- 路由注册 ---
api.add_resource(Login, '/api/login')
api.add_resource(Register, '/api/register')
api.add_resource(AdminUserResource, '/api/admin/users')

api.add_resource(TeamResource, '/api/teams')
api.add_resource(MyTeamsResource, '/api/teams/my')
api.add_resource(TeamMembersResource, '/api/teams/<int:team_id>/members')

api.add_resource(ProjectResource, '/api/projects', '/api/projects/<int:project_id>')
api.add_resource(ProjectAudit, '/api/projects/<int:project_id>/audit')
api.add_resource(TaskAssignment, '/api/projects/<int:project_id>/assign')

api.add_resource(ReviewerTasksResource, '/api/reviews/my-tasks')
api.add_resource(ReviewerIncubationProjectsResource, '/api/reviewer/incubation-projects')
api.add_resource(ReviewerReview, '/api/reviews/<int:task_id>')

api.add_resource(NotificationResource, '/api/notifications')

api.add_resource(IncubationResourceAPI, '/api/projects/<int:project_id>/incubation')
api.add_resource(ProofOfConceptResource, '/api/projects/<int:project_id>/poc')
api.add_resource(ProofOfConceptDetailResource, '/api/poc/<int:poc_id>')

# --- 7. 经费与报销管理 ---

class FundResource(Resource):
    """经费下拨管理"""
    @jwt_required()
    def post(self):
        """下拨经费（仅管理员或秘书可用）"""
        try:
            user = get_current_user()
            if user.role not in ['管理员', '秘书']:
                raise PermissionError('只有管理员或秘书可以下拨经费')
            
            data = request.get_json()
            if not data or not data.get('project_id') or not data.get('amount') or not data.get('title'):
                raise ValidationError('项目ID、金额和名目不能为空')
            
            project = Project.query.get_or_404(data['project_id'])
            
            try:
                amount = float(data['amount'])
                if amount <= 0:
                    raise ValidationError('金额必须大于0')
            except (ValueError, TypeError):
                raise ValidationError('金额格式错误')
            
            # 检查是否已存在同名经费记录
            existing = FundRecord.query.filter_by(
                project_id=data['project_id'],
                title=data['title']
            ).first()
            
            if existing:
                existing.amount += amount
            else:
                fund = FundRecord(
                    project_id=data['project_id'],
                    title=data['title'],
                    amount=amount
                )
                db.session.add(fund)
            
            db.session.commit()
            return {'message': '经费下拨成功'}, 201
        except APIException:
            raise
        except Exception as e:
            logger.error(f"下拨经费失败: {str(e)}", exc_info=True)
            db.session.rollback()
            raise APIException('下拨经费失败，请稍后重试', 500)


class ExpenditureResource(Resource):
    """支出报销管理"""
    @jwt_required()
    def post(self):
        """提交报销（仅项目参与者可用）"""
        try:
            uid = get_jwt_identity()
            user = get_current_user()
            
            if user.role != '项目参与者':
                raise PermissionError('只有项目参与者可以提交报销')
            
            data = request.get_json()
            if not data or not data.get('project_id') or not data.get('amount') or not data.get('title'):
                raise ValidationError('项目ID、金额和名目不能为空')
            
            project = Project.query.get_or_404(data['project_id'])
            
            # 检查是否为项目成员（负责人或团队成员）
            is_member = False
            if str(project.principal_id) == str(uid):
                is_member = True
            else:
                my_team_ids = db.session.query(UserInTeam.team_id).filter_by(user_id=uid).all()
                my_team_ids = [tid[0] for tid in my_team_ids]
                if project.team_id in my_team_ids:
                    is_member = True
            
            if not is_member:
                raise PermissionError('只有项目成员可以提交报销')
            
            try:
                amount = float(data['amount'])
                if amount <= 0:
                    raise ValidationError('金额必须大于0')
            except (ValueError, TypeError):
                raise ValidationError('金额格式错误')
            
            # 计算总经费和总支出
            total_funds_result = db.session.query(func.sum(FundRecord.amount)).filter_by(
                project_id=data['project_id']
            ).scalar()
            total_funds = float(total_funds_result) if total_funds_result else 0.0
            
            total_expenditures_result = db.session.query(func.sum(Expenditure.amount)).filter_by(
                project_id=data['project_id']
            ).scalar()
            total_expenditures = float(total_expenditures_result) if total_expenditures_result else 0.0
            
            # 检查余额是否足够
            balance = total_funds - total_expenditures
            if amount > balance:
                raise ValidationError(f'经费余额不足，当前余额：{balance:.2f}元，申请金额：{amount:.2f}元')
            
            # 检查是否已存在同名支出记录
            existing = Expenditure.query.filter_by(
                project_id=data['project_id'],
                title=data['title']
            ).first()
            
            if existing:
                existing.amount += amount
            else:
                expenditure = Expenditure(
                    project_id=data['project_id'],
                    title=data['title'],
                    amount=amount
                )
                db.session.add(expenditure)
            
            db.session.commit()
            return {'message': '报销提交成功'}, 201
        except APIException:
            raise
        except Exception as e:
            logger.error(f"提交报销失败: {str(e)}", exc_info=True)
            db.session.rollback()
            raise APIException('提交报销失败，请稍后重试', 500)


class ProjectFundsResource(Resource):
    """项目经费详情"""
    @jwt_required()
    def get(self, project_id):
        """获取项目的经费详情"""
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
                raise PermissionError('无权查看此项目的经费信息')
            
            # 获取所有经费下拨记录
            fund_records = FundRecord.query.filter_by(project_id=project_id).all()
            total_funds_result = db.session.query(func.sum(FundRecord.amount)).filter_by(
                project_id=project_id
            ).scalar()
            total_funds = float(total_funds_result) if total_funds_result else 0.0
            
            # 获取所有支出记录
            expenditure_records = Expenditure.query.filter_by(project_id=project_id).all()
            total_expenditures_result = db.session.query(func.sum(Expenditure.amount)).filter_by(
                project_id=project_id
            ).scalar()
            total_expenditures = float(total_expenditures_result) if total_expenditures_result else 0.0
            
            balance = total_funds - total_expenditures
            usage_rate = (total_expenditures / total_funds * 100) if total_funds > 0 else 0
            
            return {
                'total_funds': total_funds,
                'total_expenditures': total_expenditures,
                'balance': balance,
                'usage_rate': round(usage_rate, 2),
                'fund_records': [{
                    'fund_id': f.fund_id,
                    'title': f.title,
                    'amount': float(f.amount) if f.amount else 0.0
                } for f in fund_records],
                'expenditure_records': [{
                    'expenditure_id': e.expenditure_id,
                    'title': e.title,
                    'amount': float(e.amount) if e.amount else 0.0
                } for e in expenditure_records]
            }
        except APIException:
            raise
        except Exception as e:
            logger.error(f"获取经费详情失败: {str(e)}", exc_info=True)
            raise APIException('获取经费详情失败，请稍后重试', 500)


api.add_resource(FundResource, '/api/funds')
api.add_resource(ExpenditureResource, '/api/expenditures')
api.add_resource(ProjectFundsResource, '/api/projects/<int:project_id>/funds')

# --- 8. 成果与绩效管理 ---

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


api.add_resource(AchievementResource, '/api/achievements')
api.add_resource(ProjectAchievementsResource, '/api/projects/<int:project_id>/achievements')

# --- 9. 项目里程碑管理 ---

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


api.add_resource(ProjectMilestonesResource, '/api/projects/<int:project_id>/milestones')
api.add_resource(MilestoneUpdateResource, '/api/milestones/<int:milestone_id>')

# --- 10. 孵化期沟通留言 ---

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


# --- 11. 企业支持者对接 ---

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


# 注册路由
api.add_resource(ProjectCommentsResource, '/api/projects/<int:project_id>/comments')
api.add_resource(SupporterProjectsResource, '/api/supporter/projects')
api.add_resource(SupportIntentionResource, '/api/support/intentions')
api.add_resource(ProjectIntentionsResource, '/api/projects/<int:project_id>/intentions')

# --- 12. 孵化资源集市 ---

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
            
            query = IncubationResource.query.filter_by(status='开放中')
            if resource_type:
                query = query.filter_by(resource_type=resource_type)
            
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


# 注册路由
api.add_resource(SupporterResourcesResource, '/api/supporter/resources', '/api/supporter/my-resources')
api.add_resource(ResourceApplicationsResource, '/api/resources/<int:resource_id>/applications')
api.add_resource(ApplicationHandleResource, '/api/applications/<int:application_id>/handle')
api.add_resource(PublicResourcesResource, '/api/public/resources')
api.add_resource(ResourceApplyResource, '/api/resources/<int:resource_id>/apply')
api.add_resource(MyResourceApplicationsResource, '/api/my/resource-applications')

# --- 13. 数据统计与可视化 ---

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
            from datetime import timedelta
            twelve_months_ago = datetime.now() - timedelta(days=365)
            # 使用原生SQL的date_format（MySQL）
            from sqlalchemy import text
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


# 注册统计路由
api.add_resource(StatisticsResource, '/api/statistics')
api.add_resource(UserStatisticsResource, '/api/statistics/user')
api.add_resource(ReviewerStatisticsResource, '/api/statistics/reviewer')
api.add_resource(SupporterStatisticsResource, '/api/statistics/supporter')

if __name__ == '__main__':
    app.run(debug=True, port=5000)
