"""
Flask应用主入口
只包含应用初始化和错误处理
所有业务逻辑已拆分到resources模块
"""
import logging
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_restful import Api
from flask_migrate import Migrate

from config import Config
from models import db
from exceptions import APIException
from routes import register_routes

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建Flask应用
app = Flask(__name__)
app.config.from_object(Config)

# 初始化扩展
db.init_app(app)
migrate = Migrate(app, db)
jwt = JWTManager(app)
CORS(app)
api = Api(app)

# 注册路由
register_routes(api)

# 全局错误处理器
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


if __name__ == '__main__':
    app.run(debug=True, port=5000)
