"""
自定义异常类
"""
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
