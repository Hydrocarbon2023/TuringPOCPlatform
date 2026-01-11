"""
经费管理API资源
"""
import logging
from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_restful import Resource
from sqlalchemy import func

from models import db, User, UserInTeam, Project, FundRecord, Expenditure
from exceptions import ValidationError, PermissionError, APIException
from utils import get_current_user

logger = logging.getLogger(__name__)


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
