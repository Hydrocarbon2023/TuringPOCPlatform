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


class Register(Resource):
    def post(self):
        data = request.get_json()
        user = User.query.filter_by(user_name=data['user_name']).first()
        if user:
            return {'message': '用户名已存在，换一个吧TT'}, 400
        new_user = User(
            user_name=data['user_name'],
            real_name=data.get('real_name'),
            role=data['role'],
            affiliation=data.get('affiliation'),
            email=data.get('email'),
            user_profile=data.get('user_profile'),
        )
        new_user.set_password(data['password'])
        db.session.add(new_user)
        db.session.commit()
        return {'message': '用户注册成功！'}, 201


class Login(Resource):
    def post(self):
        data = request.get_json()
        user = User.query.filter_by(user_name=data['user_name']).first()
        if user and user.check_password(data['password']):
            access_token = create_access_token(identity=str(user.user_id))
            return {'token': access_token,
                    'role': user.role,
                    'user_name': user.user_name}
        return {'message': '用户名或密码错误TT'}, 401


class TeamResource(Resource):
    @jwt_required()
    def post(self):
        data = request.get_json()
        new_team = Team(
            team_name=data['team_name'],
            leader_id=get_jwt_identity(),
            domain=data.get('domain'),
            team_profile=data.get('team_profile'),
        )
        db.session.add(new_team)
        db.session.commit()
        return {'message': '团队创建成功！', 'team_id': new_team.team_id}, 201

    @jwt_required()
    def get(self, team_id=None):
        if team_id:
            team = Team.query.get(team_id)
            return {
                'team_name': team.team_name,
                'domain': team.domain,
                'team_profile': team.team_profile,
            } if team else {'message': '未找到团队TT'}, 404
        teams = Team.query.all()
        return [{'team_id': t.team_id, 'team_name': t.team_name} for t in teams]


class JoinTeam(Resource):
    @jwt_required()
    def post(self, team_id):
        user_id = get_jwt_identity()
        has_joint = UserInTeam.query.filter_by(user_id=user_id,
                                               team_id=team_id).first()
        if has_joint:
            return {'message': '已经加入该团队'}, 400
        new_join = UserInTeam(
            user_id=user_id,
            team_id=team_id,
        )
        db.session.add(new_join)
        db.session.commit()
        return {'message': '成功加入团队！'}, 201


class TeamDetail(Resource):
    @jwt_required()
    def get(self, team_id):
        team = Team.query.get_or_404(team_id)
        members = (
            db.session.query(User.real_name, User.user_id).join(UserInTeam)
            .filter(UserInTeam.team_id == team_id).all()
        )
        return {
            'team_name': team.team_name,
            'domain': team.domain,
            'team_profile': team.team_profile,
            'members': [{'id': m.user_id, 'name': m.real_name} for m in members]
        }

    @jwt_required()
    def put(self, team_id):
        data = request.get_json()
        team = Team.query.get_or_404(team_id)
        team.team_name = data.get('team_name', team.team_name)
        team.domain = data.get('domain', team.domain)
        team.team_profile = data.get('team_profile', team.team_profile)
        db.session.commit()
        return {'message': '团队信息更新成功！'}


class QuitTeam(Resource):
    @jwt_required()
    def delete(self, team_id):
        uid = get_jwt_identity()
        record = UserInTeam.query.filter_by(user_id=uid, team_id=team_id).first()
        if record:
            db.session.delete(record)
            db.session.commit()
            return {'message': '已退出团队'}
        return {'message': '退出失败，请检查是否加入过团队'}, 404


class ProjectResource(Resource):
    @jwt_required()
    def post(self):
        data = request.get_json()
        current_user_id = get_jwt_identity()
        tid = data.get('team_id', 1)
        current_team = Team.query.get(tid)

        if not current_team:
            default_team = Team(
                team_name='新团队',
                leader_id=current_user_id,
                domain='暂未确定',
                team_profile='这个团队很懒，什么都没有写',
            )
            db.session.add(default_team)
            db.session.flush()
            tid = default_team.team_id

        new_project = Project(
            project_name=data['project_name'],
            team_id=tid,
            principal_id=get_jwt_identity(),
            domain = data['domain'],
            maturity_level = data['maturity_level'],
            project_description=data.get('project_description'),
            status='待初审',
        )
        db.session.add(new_project)
        db.session.commit()
        return {'message': '项目申报成功，请等待初审',
                'project_id': new_project.project_id}, 201

    @jwt_required()
    def get(self, project_id=None):
        if project_id:
            project = Project.query.get(project_id)
            return {
                'project_name': project.project_name,
                'domain': project.domain,
                'maturity_level': project.maturity_level,
                'status': project.status,
                'project_description': project.project_description,
            } if project else {'message': '未找到项目TT'}, 404
        projects = Project.query.all()
        return [{'project_id': p.project_id,
                 'project_name': p.project_name} for p in projects]


class FundRecordResource(Resource):
    @jwt_required()
    def post(self, project_id):
        data = request.get_json()
        new_fund = FundRecord(
            project_id=project_id,
            title=data.get('title'),
            amount=data['amount'],
        )
        db.session.add(new_fund)
        db.session.commit()
        return {'message': '已发送经费申请', 'fund_id': new_fund.fund_id}, 201


class ExpenditureResource(Resource):
    @jwt_required()
    def post(self, project_id):
        data = request.get_json()
        new_expenditure = Expenditure(
            project_id=project_id,
            title=data.get('title'),
            amount=data['amount'],
        )
        db.session.add(new_expenditure)
        db.session.commit()
        return {'message': '已上传支出记录',
                'expenditure_id': new_expenditure.expenditure_id}, 201


class UserAdmin(Resource):
    @jwt_required()
    def get(self):
        users = User.query.all()
        return [{
            'user_id': u.user_id,
            'user_name': u.user_name,
            'real_name': u.real_name,
            'role': u.role,
            'affiliation': u.affiliation,
            'email': u.email,
        } for u in users]


class ProjectAudit(Resource):
    @jwt_required()
    def post(self, project_id):
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        if user.role not in ['管理员', '秘书']:
            return {'message': '权限不足'}, 403

        data = request.get_json()
        project = Project.query.get_or_404(project_id)

        new_audit = AuditRecord(
            project_id=project_id,
            auditor_id=current_user_id,
            audit_type=data['audit_type'],
            result=data['result'],
            comment=data.get('comment')
        )
        db.session.add(new_audit)

        if data['result'] == '通过':
            if project.status == '待初审':
                project.status = '初审中'
            elif project.status == '复审中':
                project.status = '公示中'
        else:
            project.status = '已取消'

        notify = Notification(
            title=f'项目“{project.project_name}”审核更新',
            user_id=project.principal_id,
            content=f'您的项目审核结果为：{data["result"]}。'
                    f'备注：{data.get("comment")}'
        )
        db.session.add(notify)

        db.session.commit()
        return {'message': '审核完成'}, 201


class TaskAssignment(Resource):
    @jwt_required()
    def post(self, project_id):
        data = request.get_json()
        # 实际开发中需校验expert_id对应的用户是否为“评审人”角色
        new_task = ReviewTask(
            project_id=project_id,
            expert_id=data['expert_id'],
            deadline=data.get('deadline'),
            status='待确认'
        )
        db.session.add(new_task)
        db.session.commit()
        return {'message': '已分配评审专家'}, 201


class ExpertReview(Resource):
    @jwt_required()
    def post(self, task_id):
        current_user = get_jwt_identity()
        task = ReviewTask.query.get_or_404(task_id)

        if str(task.expert_id) != str(current_user):
            return {'message': '无权操作此任务！'}, 403

        data = request.get_json()

        total = (int(data['innovation']) + int(data['potentiality']) +
                 int(data['feasibility']) + int(data['teamwork']))

        opinion = ReviewOpinion(
            task_id=task_id,
            innovation_score=data['innovation'],
            potentiality_score=data['potentiality'],
            feasibility_score=data['feasibility'],
            teamwork_score=data['teamwork'],
            total_score=total,
            comment=data['comment']
        )

        task.status = '已完成'
        db.session.add(opinion)
        db.session.commit()
        return {'message': '评审意见已提交'}, 201


class ProjectAchievement(Resource):
    @jwt_required()
    def post(self, project_id):
        data = request.get_json()
        new_ach = Achievement(
            title=data['title'],
            type=data['type'],
            source_information=data.get('source_information')
        )
        db.session.add(new_ach)
        db.session.flush()

        link = AchievementOfProject(
            achievement_id=new_ach.achievement_id,
            project_id=project_id
        )
        db.session.add(link)
        db.session.commit()
        return {'message': '成果登记成功！'}, 201


class UserNotifications(Resource):
    @jwt_required()
    def get(self):
        uid = get_jwt_identity()
        notifs = (Notification.query.filter_by(user_id=uid, is_read=False)
                  .order_by(Notification.create_time.desc()).all())
        return [{
            'id': n.notification_id,
            'title': n.title,
            'content': n.content,
            'time': str(n.create_time)
        } for n in notifs]

    @jwt_required()
    def put(self, notification_id):
        n = Notification.query.get_or_404(notification_id)
        if str(n.user_id) == get_jwt_identity():
            n.is_read = True
            db.session.commit()
            return {'message': '已读'}


api.add_resource(Register, '/api/register')
api.add_resource(Login, '/api/login')
api.add_resource(TeamResource, '/api/teams', '/api/teams/<int:team_id>')
api.add_resource(JoinTeam, '/api/teams/<int:team_id>/join')
api.add_resource(TeamDetail, '/api/teams/<int:team_id>')
api.add_resource(QuitTeam, '/api/teams/<int:team_id>/quit')
api.add_resource(ProjectResource, '/api/projects',
                 '/api/projects/<int:project_id>')
api.add_resource(FundRecordResource,
                 '/api/projects/<int:project_id>/fund')
api.add_resource(ExpenditureResource,
                 '/api/projects/<int:project_id>/expenditure')
api.add_resource(UserAdmin, '/api/admin/users')

if __name__ == '__main__':
    app.run(debug=True)
