import bcrypt
import logging
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import (JWTManager, create_access_token,
                                get_jwt_identity, jwt_required)
from flask_restful import Api, Resource
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_, func
from sqlalchemy.orm import joinedload
from datetime import datetime

from config import Config
from models import (db, User, Team, UserInTeam, Project, FundRecord,
                    Expenditure, ReviewTask, ReviewOpinion, AuditRecord,
                    Achievement, AchievementOfProject, Notification)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)
jwt = JWTManager(app)
CORS(app)
api = Api(app)

with app.app_context():
    db.create_all()


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
            
            new_user = User(
                user_name=data['user_name'],
                real_name=data.get('real_name'),
                role='项目参与者',
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
                raise PermissionError('只有秘书有权分配专家')

            data = request.get_json()
            if not data or 'expert_id' not in data:
                raise ValidationError('专家ID不能为空')
            
            expert_id = data['expert_id']

            if ReviewTask.query.filter_by(project_id=project_id, expert_id=expert_id).first():
                raise ValidationError('该专家已分配')

            deadline = None
            if data.get('deadline'):
                try:
                    deadline = datetime.strptime(data['deadline'], '%Y-%m-%d')
                except ValueError:
                    raise ValidationError('截止日期格式错误，应为 YYYY-MM-DD')

            task = ReviewTask(
                project_id=project_id,
                expert_id=expert_id,
                deadline=deadline,
                status='待确认'
            )
            db.session.add(task)
            db.session.commit()
            return {'message': '专家分配成功'}, 201
        except APIException:
            raise
        except Exception as e:
            logger.error(f"分配专家失败: {str(e)}", exc_info=True)
            db.session.rollback()
            raise APIException('分配专家失败，请稍后重试', 500)


# --- 5. 专家评审 ---

class ExpertTasksResource(Resource):
    @jwt_required()
    def get(self):
        uid = get_jwt_identity()
        tasks = db.session.query(ReviewTask, Project).join(Project, ReviewTask.project_id == Project.project_id) \
            .filter(ReviewTask.expert_id == uid).all()

        return [{
            'task_id': t.ReviewTask.task_id,
            'project_id': t.Project.project_id,
            'project_name': t.Project.project_name,
            'domain': t.Project.domain,
            'deadline': str(t.ReviewTask.deadline) if t.ReviewTask.deadline else '无',
            'status': t.ReviewTask.status
        } for t in tasks]


class ExpertReview(Resource):
    @jwt_required()
    def post(self, task_id):
        try:
            uid = get_jwt_identity()
            task = ReviewTask.query.get_or_404(task_id)
            if str(task.expert_id) != str(uid):
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

api.add_resource(ExpertTasksResource, '/api/reviews/my-tasks')
api.add_resource(ExpertReview, '/api/reviews/<int:task_id>')

api.add_resource(NotificationResource, '/api/notifications')

if __name__ == '__main__':
    app.run(debug=True, port=5000)
