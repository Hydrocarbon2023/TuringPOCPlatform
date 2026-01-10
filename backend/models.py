from datetime import datetime

import bcrypt
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = 'User'
    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_name = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    real_name = db.Column(db.String(50))
    role = db.Column(db.Enum('项目参与者', '评审人', '秘书', '管理员'),
                     nullable=False)
    affiliation = db.Column(db.String(50))
    email = db.Column(db.String(50))
    user_profile = db.Column(db.Text)

    def set_password(self, password):
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'),
                                           bcrypt.gensalt()).decode('utf-8')

    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'),
                              self.password_hash.encode('utf-8'))


class Team(db.Model):
    __tablename__ = 'Team'
    team_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    team_name = db.Column(db.String(50))
    leader_id = db.Column(db.Integer, db.ForeignKey('User.user_id'))
    domain = db.Column(db.String(50))
    team_profile = db.Column(db.Text)


class UserInTeam(db.Model):
    __tablename__ = 'UserInTeam'
    record_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('User.user_id'),
                        nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey('Team.team_id'),
                        nullable=False)


class Project(db.Model):
    __tablename__ = 'Project'
    project_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    project_name = db.Column(db.String(100), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey('Team.team_id'),
                        nullable=False)
    principal_id = db.Column(db.Integer, db.ForeignKey('User.user_id'),
                             nullable=False)
    domain = db.Column(db.String(50))
    maturity_level = db.Column(db.Enum('研发阶段', '小试阶段', '中试阶段',
                                       '小批量生产阶段'), nullable=False)
    submit_time = db.Column(db.DateTime, default=datetime.now)
    status = db.Column(db.Enum('待初审', '初审中', '复审中',
                               '公示中', '已通过', '孵化中', '概念验证中', 
                               '孵化完成', '已取消'), nullable=False)
    project_description = db.Column(db.Text)


class FundRecord(db.Model):
    __tablename__ = 'FundRecord'
    fund_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    project_id = db.Column(db.Integer, db.ForeignKey('Project.project_id'),
                           nullable=False)
    title = db.Column(db.String(50))
    amount = db.Column(db.Numeric(12, 2), default=0.00)
    __table_args__ = tuple(db.UniqueConstraint('project_id', 'title'))


class Expenditure(db.Model):
    __tablename__ = 'Expenditure'
    expenditure_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    project_id = db.Column(db.Integer, db.ForeignKey('Project.project_id'),
                           nullable=False)
    title = db.Column(db.String(50))
    amount = db.Column(db.Numeric(12, 2), default=0.00)
    __table_args__ = tuple(db.UniqueConstraint('project_id', 'title'))


class ReviewTask(db.Model):
    __tablename__ = 'ReviewTask'
    task_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    project_id = db.Column(db.Integer, db.ForeignKey('Project.project_id'),
                           nullable=False)
    reviewer_id = db.Column(db.Integer, db.ForeignKey('User.user_id'))
    assign_time = db.Column(db.DateTime, default=datetime.now)
    deadline = db.Column(db.DateTime)
    status = db.Column(db.Enum('待确认', '进行中', '已完成'), default='待确认')


class ReviewOpinion(db.Model):
    __tablename__ = 'ReviewOpinion'
    opinion_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    task_id = db.Column(db.Integer, db.ForeignKey('ReviewTask.task_id'),
                        nullable=False)
    innovation_score = db.Column(db.SmallInteger, default=0)
    potentiality_score = db.Column(db.SmallInteger, default=0)
    feasibility_score = db.Column(db.SmallInteger, default=0)
    teamwork_score = db.Column(db.SmallInteger, default=0)
    total_score = db.Column(db.SmallInteger, default=0)
    submit_time = db.Column(db.DateTime, default=datetime.now)
    comment = db.Column(db.Text)


class AuditRecord(db.Model):
    __tablename__ = 'AuditRecord'
    record_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    project_id = db.Column(db.Integer, db.ForeignKey('Project.project_id'),
                           nullable=False)
    auditor_id = db.Column(db.Integer, db.ForeignKey('User.user_id'))
    audit_type = db.Column(db.Enum('项目初审', '复审遴选', '经费审核'),
                           nullable=False)
    result = db.Column(db.Enum('通过', '未通过'))
    submit_time = db.Column(db.DateTime, default=datetime.now)
    comment = db.Column(db.Text)


class Achievement(db.Model):
    __tablename__ = 'Achievement'
    achievement_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(100))
    type = db.Column(db.String(20))
    publish_time = db.Column(db.DateTime, default=datetime.now)
    source_information = db.Column(db.Text)


class AchievementOfProject(db.Model):
    __tablename__ = 'AchievementOfProject'
    record_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    achievement_id = db.Column(db.Integer,
                               db.ForeignKey('Achievement.achievement_id'),
                               nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('Project.project_id'),
                           nullable=False)


class Notification(db.Model):
    __tablename__ = 'Notification'
    notification_id = db.Column(db.Integer, primary_key=True,
                                autoincrement=True)
    title = db.Column(db.String(100))
    user_id = db.Column(db.Integer, db.ForeignKey('User.user_id'),
                        nullable=False)
    content = db.Column(db.Text)
    create_time = db.Column(db.DateTime, default=datetime.now)
    is_read = db.Column(db.Boolean, default=False)
    redirect_url = db.Column(db.String(255))


class IncubationRecord(db.Model):
    """产业孵化记录"""
    __tablename__ = 'IncubationRecord'
    incubation_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    project_id = db.Column(db.Integer, db.ForeignKey('Project.project_id'),
                           nullable=False)
    start_time = db.Column(db.DateTime, default=datetime.now)
    planned_end_time = db.Column(db.DateTime)
    actual_end_time = db.Column(db.DateTime)
    status = db.Column(db.Enum('计划中', '进行中', '已完成', '已暂停'), 
                       default='计划中', nullable=False)
    progress = db.Column(db.SmallInteger, default=0)  # 进度百分比 0-100
    incubation_plan = db.Column(db.Text)  # 孵化计划
    milestones = db.Column(db.Text)  # 里程碑（JSON格式存储）
    resources = db.Column(db.Text)  # 资源需求
    challenges = db.Column(db.Text)  # 面临的挑战
    achievements = db.Column(db.Text)  # 取得的成果
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)


class ProofOfConcept(db.Model):
    """概念验证记录"""
    __tablename__ = 'ProofOfConcept'
    poc_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    project_id = db.Column(db.Integer, db.ForeignKey('Project.project_id'),
                           nullable=False)
    incubation_id = db.Column(db.Integer, db.ForeignKey('IncubationRecord.incubation_id'))
    title = db.Column(db.String(200), nullable=False)  # 验证标题
    description = db.Column(db.Text)  # 验证描述
    verification_objective = db.Column(db.Text)  # 验证目标
    verification_method = db.Column(db.Text)  # 验证方法
    verification_result = db.Column(db.Text)  # 验证结果
    status = db.Column(db.Enum('待开始', '进行中', '已完成', '已验证', '未通过'),
                       default='待开始', nullable=False)
    start_time = db.Column(db.DateTime, default=datetime.now)
    end_time = db.Column(db.DateTime)
    evidence_files = db.Column(db.Text)  # 证据文件（JSON格式存储）
    metrics = db.Column(db.Text)  # 关键指标（JSON格式存储）
    conclusion = db.Column(db.Text)  # 结论
    create_time = db.Column(db.DateTime, default=datetime.now)
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
