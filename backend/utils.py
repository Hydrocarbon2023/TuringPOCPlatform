"""
辅助函数
"""
from flask_jwt_extended import get_jwt_identity
from datetime import datetime, timedelta
from models import db, User, Milestone
from exceptions import NotFoundError


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
                'deliverable': '完成中期进展汇报，提交中期报告'
            },
            {
                'title': '结项验收',
                'due_date': base_date + timedelta(days=365),
                'status': '未开始',
                'deliverable': '完成最终成果展示，提交结项报告'
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
        
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        # 静默处理，避免影响主流程
        pass
