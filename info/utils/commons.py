# 导入flask内置的session对象
from flask import session, current_app, g
from info.models import User


# 自定义过滤器
def index_filter(index):
    if index == 1:
        return 'first'
    elif index == 2:
        return 'second'
    elif index == 3:
        return 'third'
    else:
        return ''

import functools

# 自定义装饰器，检查用户登录状态
def login_required(f):
    @functools.wraps(f)
    def wrapper(*args,**kwargs):
        user_id = session.get('user_id')
        user = None
        # 判断user_id
        if user_id:
            try:
                user = User.query.filter_by(id=user_id).first()
            except Exception as e:
                current_app.logger.error(e)
        # 使用g对象存储user信息
        g.user = user
        return f(*args,**kwargs)

    # wrapper.__name__ = f.__name__
    return wrapper


