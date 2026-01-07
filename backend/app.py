from datetime import datetime

import bcrypt
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import (JWTManager, create_access_token,
                                get_jwt_identity, jwt_required)
from flask_restful import Api, Resource
from flask_sqlalchemy import SQLAlchemy

from config import Config
from models import (db, User, Team, UserInTeam, Project, FundRecord,
                    Expenditure, ReviewTask, ReviewOpinion, AuditRecord,
                    Achievement, AchievementOfProject, Notification)

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)
jwt = JWTManager(app)
CORS(app)
api = Api(app)

with app.app_context():
    db.create_all()


# --- 辅助函数：权限检查 ---
def get_current_user():
    uid = get_jwt_identity()
    return User.query.get(uid)


# --- 1. 认证与用户管理 ---

class Login(Resource):
    def post(self):
        data = request.get_json()
        user = User.query.filter_by(user_name=data['user_name']).first()
        if user and user.check_password(data['password']):
            access_token = create_access_token(identity=str(user.user_id))
            return {'token': access_token, 'role': user.role, 'user_name': user.user_name, 'real_name': user.real_name}
        return {'message': '用户名或密码错误'}, 401


class Register(Resource):
    # 公开注册接口 (通常用于项目参与者)
    def post(self):
        data = request.get_json()
        if User.query.filter_by(user_name=data['user_name']).first():
            return {'message': '用户名已存在'}, 400
        new_user = User(
            user_name=data['user_name'],
            real_name=data.get('real_name'),
            role=data.get('role', '项目参与者'),  # 默认只能注册参与者
            affiliation=data.get('affiliation'),
            email=data.get('email')
        )
        new_user.set_password(data['password'])
        db.session.add(new_user)
        db.session.commit()
        return {'message': '注册成功'}, 201


class AdminUserResource(Resource):
    # 管理员创建用户接口
    @jwt_required()
    def post(self):
        current_user = get_current_user()
        if current_user.role != '管理员':
            return {'message': '权限不足'}, 403

        data = request.get_json()
        if User.query.filter_by(user_name=data['user_name']).first():
            return {'message': '用户名已存在'}, 400

        new_user = User(
            user_name=data['user_name'],
            real_name=data['real_name'],
            role=data['role'],  # 管理员可以指定任意角色
            affiliation=data.get('affiliation'),
            email=data.get('email')
        )
        new_user.set_password(data['password'])
        db.session.add(new_user)
        db.session.commit()
        return {'message': f'已创建用户: {data["real_name"]}'}, 201

    @jwt_required()
    def get(self):
        # 获取所有用户列表
        users = User.query.all()
        return [{
            'user_id': u.user_id,
            'user_name': u.user_name,
            'real_name': u.real_name,
            'role': u.role,
            'affiliation': u.affiliation
        } for u in users]


# --- 2. 项目管理 ---

class ProjectResource(Resource):
    @jwt_required()
    def get(self, project_id=None):
        if project_id:
            p = Project.query.get_or_404(project_id)
            principal = User.query.get(p.principal_id)
            return {
                'project_id': p.project_id,
                'project_name': p.project_name,
                'domain': p.domain,
                'status': p.status,
                'maturity_level': p.maturity_level,
                'project_description': p.project_description,
                'submit_time': str(p.submit_time),
                'principal_name': principal.real_name if principal else '未知',
                'team_id': p.team_id
            }

        # 获取所有项目（实际项目中应根据角色过滤，这里为了演示简化）
        projects = Project.query.order_by(Project.submit_time.desc()).all()
        return [{
            'project_id': p.project_id,
            'project_name': p.project_name,
            'domain': p.domain,
            'status': p.status,
            'principal_id': p.principal_id,
            # 简单查询，实际可用 join 优化
            'principal_name': User.query.get(p.principal_id).real_name if p.principal_id else ''
        } for p in projects]

    @jwt_required()
    def post(self):
        data = request.get_json()
        # 简化逻辑：如果没有Team，创建一个默认的
        uid = get_jwt_identity()

        # 检查是否有默认团队，没有则创建
        team = Team.query.filter_by(leader_id=uid).first()
        if not team:
            team = Team(team_name=f"{data.get('real_name', '用户')}的团队", leader_id=uid)
            db.session.add(team)
            db.session.flush()

        new_project = Project(
            project_name=data['project_name'],
            team_id=team.team_id,
            principal_id=uid,
            domain=data['domain'],
            maturity_level=data['maturity_level'],
            project_description=data.get('project_description'),
            status='待初审'
        )
        db.session.add(new_project)
        db.session.commit()
        return {'message': '申报成功'}, 201


# --- 3. 审核与分配流程 ---

class ProjectAudit(Resource):
    @jwt_required()
    def post(self, project_id):
        user = get_current_user()
        if user.role not in ['管理员', '秘书']:
            return {'message': '权限不足'}, 403

        data = request.get_json()
        project = Project.query.get_or_404(project_id)

        # 记录审核
        record = AuditRecord(
            project_id=project_id,
            auditor_id=user.user_id,
            audit_type=data.get('audit_type', '项目初审'),
            result=data['result'],
            comment=data.get('comment')
        )
        db.session.add(record)

        # 状态流转
        if data['result'] == '通过':
            # 初审通过后，状态变为 "复审中" (意味着可以分配专家了)
            project.status = '复审中'
        else:
            project.status = '已取消'  # 或 退回修改

        db.session.commit()
        return {'message': '审核完成'}, 201


class TaskAssignment(Resource):
    @jwt_required()
    def post(self, project_id):
        user = get_current_user()
        if user.role not in ['管理员', '秘书']:
            return {'message': '权限不足'}, 403

        data = request.get_json()
        expert_id = data['expert_id']

        # 检查是否重复分配
        exists = ReviewTask.query.filter_by(project_id=project_id, expert_id=expert_id).first()
        if exists:
            return {'message': '该专家已分配此任务'}, 400

        task = ReviewTask(
            project_id=project_id,
            expert_id=expert_id,
            deadline=datetime.strptime(data['deadline'], '%Y-%m-%d') if data.get('deadline') else None,
            status='待确认'
        )
        db.session.add(task)
        db.session.commit()
        return {'message': '专家分配成功'}, 201


# --- 4. 专家评审 ---

class ExpertTasksResource(Resource):
    @jwt_required()
    def get(self):
        uid = get_jwt_identity()
        # 获取分配给当前专家的任务，并关联项目信息
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
        uid = get_jwt_identity()
        task = ReviewTask.query.get_or_404(task_id)
        if str(task.expert_id) != str(uid):
            return {'message': '无权操作'}, 403

        data = request.get_json()
        total = int(data.get('innovation', 0)) + int(data.get('feasibility', 0)) + int(data.get('teamwork', 0))

        opinion = ReviewOpinion(
            task_id=task_id,
            innovation_score=data.get('innovation', 0),
            potentiality_score=0,
            feasibility_score=data.get('feasibility', 0),
            teamwork_score=data.get('teamwork', 0),
            total_score=total,
            comment=data.get('comment')
        )
        task.status = '已完成'
        db.session.add(opinion)
        db.session.commit()
        return {'message': '评审提交成功'}, 201


# --- 路由注册 ---
api.add_resource(Login, '/api/login')
api.add_resource(Register, '/api/register')
api.add_resource(AdminUserResource, '/api/admin/users')  # 管理员用户管理

api.add_resource(ProjectResource, '/api/projects', '/api/projects/<int:project_id>')
api.add_resource(ProjectAudit, '/api/projects/<int:project_id>/audit')  # 审核
api.add_resource(TaskAssignment, '/api/projects/<int:project_id>/assign')  # 分配

api.add_resource(ExpertTasksResource, '/api/reviews/my-tasks')  # 专家获取任务
api.add_resource(ExpertReview, '/api/reviews/<int:task_id>')  # 专家提交评审

if __name__ == '__main__':
    app.run(debug=True, port=5000)
