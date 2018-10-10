# 导入蓝图对象
from flask import session, render_template, current_app, jsonify, request, g
# 导入模型类
from info import db
from info.models import User, News, Category
# 导入自定义的状态码
from info.utils.response_code import RET
from . import news_blue
# 导入自定义的登录验证装饰器
from info.utils.commons import login_required


# 首页模板数据加载
@news_blue.route('/')
@login_required
def index():
    user = g.user
    # 新闻点击排行
    # 默认按照新闻的点击次数倒序排序
    try:
        # News.qeury.order_by(News.clicks.desc()).limit(6)
        news_list = News.query.filter().order_by(News.clicks.desc()).limit(6)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询新闻数据异常')
    # 判断查询结果是否存在
    if not news_list:
        return jsonify(errno=RET.NODATA, errmsg='无新闻数据')
    # 定义容器列表用来存储遍历后的数据
    news_dict_list = []
    # 遍历查询结果，把查询到的对象转成可读字符串
    for news in news_list:
        news_dict_list.append(news.to_dict())

    # 新闻分类数据展示
    try:
        categories = Category.query.all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询分类数据异常')
    # 判断查询结果
    if not categories:
        return jsonify(errno=RET.NODATA, errmsg='无分类数据')
    # 定义容器存储查询结果
    category_list = []
    # 遍历查询结果
    for category in categories:
        category_list.append(category.to_dict())

    # 返回数据
    data = {
        'user_info': user.to_dict() if user else None,
        'news_dict_list': news_dict_list,
        'category_list': category_list
    }

    return render_template('news/index.html', data=data)


# 项目favicon.ico文件的加载
@news_blue.route('/favicon.ico')
def favicon():
    """
    http://127.0.0.1:5000/favicon.ico
    实现/favicon.ico路径下的图标加载
    1、favicon图标的加载，不是每次请求都加载，是浏览器默认实现的，如果有缓存，必须要清除缓存，
    2、把浏览器彻底关闭，重启浏览器。
    :return:
    """
    # 使用current_app调用flask内置的函数，发送静态文件给浏览器，实现logo图标的加载
    return current_app.send_static_file('news/favicon.ico')