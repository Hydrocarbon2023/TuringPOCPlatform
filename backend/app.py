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
            access_token = create_access_token(identity=user.user_id)
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


class ProjectResource(Resource):
    @jwt_required()
    def post(self):
        data = request.get_json()
        new_project = Project(
            project_name=data['project_name'],
            team_id=data['team_id'],
            principal_id=get_jwt_identity(),
            domain = data['domain'],
            maturity_level = data['maturity_level'],
            project_description=data.get('project_description'),
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


api.add_resource(Register, '/api/register')
api.add_resource(Login, '/api/login')
api.add_resource(TeamResource, '/api/teams', '/api/teams/<int:team_id>')
api.add_resource(JoinTeam, '/api/teams/<int:team_id>/join')
api.add_resource(ProjectResource, '/api/projects',
                 '/api/projects/<int:project_id>')
api.add_resource(FundRecordResource,
                 '/api/projects/<int:project_id>/fund')
api.add_resource(ExpenditureResource,
                 '/api/projects/<int:project_id>/expenditure')

if __name__ == '__main__':
    app.run(debug=True)
