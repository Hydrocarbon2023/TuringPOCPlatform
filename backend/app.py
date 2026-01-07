import bcrypt
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import (JWTManager, create_access_token,
                                get_jwt_identity, jwt_required)
from flask_restful import Api, Resource
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_
from datetime import datetime

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


# --- 辅助函数 ---
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
            return {
                'token': access_token,
                'role': user.role,
                'user_name': user.user_name,
                'real_name': user.real_name,
                'user_id': user.user_id
            }
        return {'message': '用户名或密码错误'}, 401


class Register(Resource):
    def post(self):
        data = request.get_json()
        if User.query.filter_by(user_name=data['user_name']).first():
            return {'message': '用户名已存在'}, 400
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


class AdminUserResource(Resource):
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
            role=data['role'],
            affiliation=data.get('affiliation'),
            email=data.get('email')
        )
        new_user.set_password(data['password'])
        db.session.add(new_user)
        db.session.commit()
        return {'message': f'已创建用户: {data["real_name"]}'}, 201

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
        teams = Team.query.all()
        return [{
            'team_id': t.team_id,
            'team_name': t.team_name,
            'leader_id': t.leader_id,
            'leader_name': User.query.get(t.leader_id).user_name if t.leader_id else '未知',
            'domain': t.domain,
            'member_count': UserInTeam.query.filter_by(team_id=t.team_id).count()
        } for t in teams]

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
        teams = db.session.query(Team).join(UserInTeam).filter(UserInTeam.user_id == uid).all()
        return [{
            'team_id': t.team_id,
            'team_name': t.team_name,
            'domain': t.domain,
            'role': '队长' if str(t.leader_id) == str(uid) else '成员',
            'leader_name': User.query.get(t.leader_id).user_name if t.leader_id else '未知'
        } for t in teams]


class TeamMembersResource(Resource):
    @jwt_required()
    def post(self, team_id):
        current_uid = get_jwt_identity()
        team = Team.query.get_or_404(team_id)
        if str(team.leader_id) != str(current_uid):
            return {'message': '只有队长可以邀请成员'}, 403

        data = request.get_json()
        target_username = data.get('user_name')
        target_user = User.query.filter_by(user_name=target_username).first()

        if not target_user:
            return {'message': '用户不存在'}, 404

        exists = UserInTeam.query.filter_by(user_id=target_user.user_id, team_id=team_id).first()
        if exists:
            return {'message': '该用户已在团队中'}, 400

        new_member = UserInTeam(user_id=target_user.user_id, team_id=team_id)
        db.session.add(new_member)
        db.session.commit()
        return {'message': f'已邀请 {target_user.real_name} 加入团队'}, 201

    @jwt_required()
    def get(self, team_id):
        members = db.session.query(User).join(UserInTeam).filter(UserInTeam.team_id == team_id).all()
        team = Team.query.get(team_id)
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

        # 获取用户所在的所有团队ID
        my_team_ids = [r.team_id for r in UserInTeam.query.filter_by(user_id=uid).all()]

        # === 详情查询 (JOIN User 获取 user_name) ===
        if project_id:
            result = db.session.query(Project, User.user_name) \
                .outerjoin(User, Project.principal_id == User.user_id) \
                .filter(Project.project_id == project_id).first()

            if not result:
                return {'message': '项目不存在'}, 404

            p, principal_name = result

            is_my_project = (str(p.principal_id) == str(uid))
            is_team_member = (p.team_id in my_team_ids)
            has_permission = (is_my_project or is_team_member or user.role in ['秘书', '管理员', '评审人'])

            if not has_permission:
                return {'message': '无权查看此项目'}, 403

            review_info = {}
            if p.status in ['孵化阶段', '复审未通过']:
                opinions = db.session.query(ReviewOpinion).join(ReviewTask).filter(
                    ReviewTask.project_id == p.project_id).all()
                if opinions:
                    avg = sum(o.total_score for o in opinions) / len(opinions)
                    review_info = {'avg_score': round(avg, 1), 'review_count': len(opinions)}

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

        # === 列表查询 (JOIN User 获取 user_name) ===
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
        data = request.get_json()
        uid = get_jwt_identity()
        user = User.query.get(uid)

        # 智能团队归属逻辑
        tid = data.get('team_id')
        if not tid:
            user_teams = db.session.query(Team).join(UserInTeam).filter(UserInTeam.user_id == uid).all()
            if user_teams:
                # 优先归属到自己创建的团队
                own_team = next((t for t in user_teams if str(t.leader_id) == str(uid)), None)
                tid = own_team.team_id if own_team else user_teams[0].team_id
            else:
                # 自动创建个人团队
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


# --- 4. 秘书功能 ---

class ProjectAudit(Resource):
    @jwt_required()
    def post(self, project_id):
        user = get_current_user()
        if user.role != '秘书':
            return {'message': '只有秘书有权进行初审'}, 403

        data = request.get_json()
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


class TaskAssignment(Resource):
    @jwt_required()
    def post(self, project_id):
        user = get_current_user()
        if user.role != '秘书':
            return {'message': '只有秘书有权分配专家'}, 403

        data = request.get_json()
        expert_id = data['expert_id']

        if ReviewTask.query.filter_by(project_id=project_id, expert_id=expert_id).first():
            return {'message': '该专家已分配'}, 400

        task = ReviewTask(
            project_id=project_id,
            expert_id=expert_id,
            deadline=datetime.strptime(data['deadline'], '%Y-%m-%d') if data.get('deadline') else None,
            status='待确认'
        )
        db.session.add(task)
        db.session.commit()
        return {'message': '专家分配成功'}, 201


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
        uid = get_jwt_identity()
        task = ReviewTask.query.get_or_404(task_id)
        if str(task.expert_id) != str(uid):
            return {'message': '无权操作'}, 403

        data = request.get_json()
        total = int(data.get('innovation', 0)) + int(data.get('feasibility', 0)) + \
                int(data.get('potentiality', 0)) + int(data.get('teamwork', 0))

        opinion = ReviewOpinion(
            task_id=task_id,
            innovation_score=data.get('innovation'),
            feasibility_score=data.get('feasibility'),
            potentiality_score=data.get('potentiality'),
            teamwork_score=data.get('teamwork'),
            total_score=total,
            comment=data.get('comment')
        )
        task.status = '已完成'
        db.session.add(opinion)
        db.session.commit()

        self.check_and_finalize(task.project_id)
        return {'message': '评审已提交'}, 201

    def check_and_finalize(self, project_id):
        # 自动结算逻辑：满3人且均分>60通过
        all_tasks = ReviewTask.query.filter_by(project_id=project_id).all()
        finished_tasks = [t for t in all_tasks if t.status == '已完成']

        if len(finished_tasks) >= 3:
            opinions = db.session.query(ReviewOpinion).join(ReviewTask).filter(
                ReviewTask.project_id == project_id).all()
            avg_score = sum(op.total_score for op in opinions) / len(opinions)

            project = Project.query.get(project_id)
            if avg_score > 60:
                project.status = '孵化阶段'
                msg = f"项目通过复审（均分{avg_score:.1f}），进入孵化阶段。"
            else:
                project.status = '复审未通过'
                msg = f"项目复审未通过（均分{avg_score:.1f}）。"

            notify = Notification(user_id=project.principal_id, title="复审结果", content=msg)
            db.session.add(notify)
            db.session.commit()


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

if __name__ == '__main__':
    app.run(debug=True, port=5000)
