"""
路由注册模块
统一管理所有API路由
"""
from flask_restful import Api

# 导入所有Resource类
from resources.auth import Login, Register
from resources.users import AdminUserResource
from resources.teams import TeamResource, MyTeamsResource, TeamMembersResource
from resources.projects import ProjectResource
from resources.secretary import ProjectAudit, TaskAssignment
from resources.reviewer import (
    ReviewerTasksResource, ReviewerIncubationProjectsResource,
    ReviewerReview, NotificationResource
)
from resources.incubation import IncubationResourceAPI, ProofOfConceptResource, ProofOfConceptDetailResource
from resources.funds import FundResource, ExpenditureResource, ProjectFundsResource
from resources.achievements import AchievementResource, ProjectAchievementsResource
from resources.milestones import ProjectMilestonesResource, MilestoneUpdateResource
from resources.comments import ProjectCommentsResource
from resources.supporter import SupporterProjectsResource, SupportIntentionResource, ProjectIntentionsResource
from resources.marketplace import (
    SupporterResourcesResource, ResourceApplicationsResource, ApplicationHandleResource,
    PublicResourcesResource, ResourceApplyResource, MyResourceApplicationsResource
)
from resources.statistics import (
    StatisticsResource, UserStatisticsResource, ReviewerStatisticsResource, SupporterStatisticsResource
)


def register_routes(api: Api):
    """注册所有路由"""
    # 认证与用户管理
    api.add_resource(Login, '/api/login')
    api.add_resource(Register, '/api/register')
    api.add_resource(AdminUserResource, '/api/admin/users')
    
    # 团队管理
    api.add_resource(TeamResource, '/api/teams')
    api.add_resource(MyTeamsResource, '/api/teams/my')
    api.add_resource(TeamMembersResource, '/api/teams/<int:team_id>/members')
    
    # 项目管理
    api.add_resource(ProjectResource, '/api/projects', '/api/projects/<int:project_id>')
    api.add_resource(ProjectAudit, '/api/projects/<int:project_id>/audit')
    api.add_resource(TaskAssignment, '/api/projects/<int:project_id>/assign')
    
    # 评审人功能
    api.add_resource(ReviewerTasksResource, '/api/reviews/my-tasks')
    api.add_resource(ReviewerIncubationProjectsResource, '/api/reviewer/incubation-projects')
    api.add_resource(ReviewerReview, '/api/reviews/<int:task_id>')
    api.add_resource(NotificationResource, '/api/notifications')
    
    # 孵化管理
    api.add_resource(IncubationResourceAPI, '/api/projects/<int:project_id>/incubation')
    api.add_resource(ProofOfConceptResource, '/api/projects/<int:project_id>/poc')
    api.add_resource(ProofOfConceptDetailResource, '/api/poc/<int:poc_id>')
    
    # 经费管理
    api.add_resource(FundResource, '/api/funds')
    api.add_resource(ExpenditureResource, '/api/expenditures')
    api.add_resource(ProjectFundsResource, '/api/projects/<int:project_id>/funds')
    
    # 成果管理
    api.add_resource(AchievementResource, '/api/achievements')
    api.add_resource(ProjectAchievementsResource, '/api/projects/<int:project_id>/achievements')
    
    # 里程碑管理
    api.add_resource(ProjectMilestonesResource, '/api/projects/<int:project_id>/milestones')
    api.add_resource(MilestoneUpdateResource, '/api/milestones/<int:milestone_id>')
    
    # 评论管理
    api.add_resource(ProjectCommentsResource, '/api/projects/<int:project_id>/comments')
    
    # 企业支持者
    api.add_resource(SupporterProjectsResource, '/api/supporter/projects')
    api.add_resource(SupportIntentionResource, '/api/support/intentions')
    api.add_resource(ProjectIntentionsResource, '/api/projects/<int:project_id>/intentions')
    
    # 资源集市
    api.add_resource(SupporterResourcesResource, '/api/supporter/resources', '/api/supporter/my-resources')
    api.add_resource(ResourceApplicationsResource, '/api/resources/<int:resource_id>/applications')
    api.add_resource(ApplicationHandleResource, '/api/applications/<int:application_id>/handle')
    api.add_resource(PublicResourcesResource, '/api/public/resources')
    api.add_resource(ResourceApplyResource, '/api/resources/<int:resource_id>/apply')
    api.add_resource(MyResourceApplicationsResource, '/api/my/resource-applications')
    
    # 统计
    api.add_resource(StatisticsResource, '/api/statistics')
    api.add_resource(UserStatisticsResource, '/api/statistics/user')
    api.add_resource(ReviewerStatisticsResource, '/api/statistics/reviewer')
    api.add_resource(SupporterStatisticsResource, '/api/statistics/supporter')
