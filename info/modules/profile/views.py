from flask import g, redirect, render_template, request, jsonify, current_app, session
import uuid
from . import profile_blue
from info.utils.commons import login_required
from info.utils.response_code import RET
from info import db,constants
# 导入阿里云
from info.utils.image_storage import storage
# 导入模型类
from info.models import Category,News


@profile_blue.route("/info")
@login_required
def user_info():
    """
    个人中心基本资料展示
    1、尝试获取用户信息
    # user = g.user
    2、如果用户未登录，重定向到项目首页
    3、如果用户登录，获取用户信息
    4、把用户信息传给模板
    :return:
    """
    user = g.user
    if not user:
        return redirect('/')
    data = {
        'user_info':user.to_dict()
    }
    return render_template('news/user.html',data=data)


@profile_blue.route("/base_info",methods=['GET','POST'])
@login_required
def base_info():
    """
    基本资料的展示和修改
    1、尝试获取用户信息
    2、如果是get请求，返回用户信息给模板
    如果是post请求：
    1、获取参数，nick_name,signature,gender[MAN,WOMAN]
    2、检查参数的完整性
    3、检查gender性别必须在范围内
    4、保存用户信息
    5、提交数据
    6、修改redis缓存中的nick_name
    注册：session['nick_name'] = mobile
    登录：session['nick_name'] = user.nick_name
    修改：session['nick_name'] = nick_name

    7、返回结果


    :return:
    """
    user = g.user
    if request.method == 'GET':

        data = {
            'user': user.to_dict()
        }
        return render_template('news/user_base_info.html', data=data)
    # 获取参数
    nick_name = request.json.get('nick_name')
    signature = request.json.get('signature')
    gender = request.json.get('gender')
    # 检查参数
    if not all([nick_name,signature,gender]):
        return jsonify(errno=RET.PARAMERR,errmsg='参数缺失')
    # 校验性别参数范围
    if gender not in ['MAN','WOMAN']:
        return jsonify(errno=RET.PARAMERR,errmsg='参数范围错误')
    # 保存用户信息
    user.nick_name = nick_name
    user.signature = signature
    user.gender = gender
    # 提交数据
    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR,errmsg='保存数据失败')
    # 修改redis缓存中的用户信息
    session['nick_name'] = nick_name
    # 返回结果
    return jsonify(errno=RET.OK,errmsg='OK')


@profile_blue.route("/pic_info",methods=['GET','POST'])
@login_required
def save_avatar():
    """
    保存用户头像
    获取用户信息，如果是get请求，user.to_dict()加载模板
    1、获取参数，
    avatar = request.files.get('avatar')
    文件对象：具有读写方法的对象
    2、检查参数
    3、读取文件对象
    4、调用七牛云，上传头像，保存七牛云返回的图片名称
    name = storage(image)
    5、保存用户头像数据，提交到mysql中是图片名称
    6、拼接图片的完整的绝对路径
    外链域名+图片名称：http://p8m0n4bb5.bkt.clouddn.com/图片名称
    7、返回结果

    :return:
    """
    user = g.user
    if request.method == 'GET':
        data = {
            'user':user.to_dict()
        }
        return render_template('news/user_pic_info.html',data=data)
    # 获取文件参数
    avatar = request.files.get('avatar')
    # 检查参数
    if not avatar:
        return jsonify(errno=RET.PARAMERR,errmsg='参数错误')
    # # 读取图片数据，转换成bytes类型
    # try:
    #     image_data = avatar.read()
    # except Exception as e:
    #     current_app.logger.error(e)
    #     return jsonify(errno=RET.PARAMERR,errmsg='参数格式错误')
    # # 调用七牛云，上传图片,
    try:
        file_name = str(uuid.uuid1())+"_" + avatar.filename
        image_name = storage(avatar.read(), file_name)
        # print(image_name)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR,errmsg='上传图片失败')
    # 保存图片文件的名称到mysql数据库中
    user.avatar_url = image_name
    # 提交数据
    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR,errmsg='保存数据失败')
    # 拼接图片的绝对路径，返回前端
    avatar_url = constants.IMG_DOMIN_PREFIX + image_name
    data = {
        'avatar_url':avatar_url
    }
    # 返回数据
    return jsonify(errno=RET.OK,errmsg='OK',data=data)


@profile_blue.route('/news_release',methods=['GET','POST'])
@login_required
def news_release():
    """
    新闻发布：
    如果是get请求，加载新闻分类，需要移除'最新'分类，传给模板
    :return:
    """
    user = g.user
    if not user:
        return jsonify(errno=RET.SESSIONERR,errmsg='用户未登录')

    if request.method == 'GET':
        try:
            category_list = Category.query.all()
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR,errmsg='查询新闻分类数据失败')
        # 判断查询结果
        if not category_list:
            return jsonify(errno=RET.NODATA,errmsg='无新闻分类数据')
        categories = []
        for category in category_list:
            categories.append(category.to_dict())
        # 移除最新
        categories.pop(0)
        data = {
            'categories':categories
        }
        return render_template('news/user_news_release.html',data=data)

    # 如果不是get请求，获取参数,title,category_id,digest,index_image,content
    title = request.form.get('title')
    category_id = request.form.get('category_id')
    digest = request.form.get('digest')
    index_image = request.files.get('index_image')
    content = request.form.get('content')
    # 检查参数的完整性
    if not all([title,category_id,digest,index_image,content]):
        return jsonify(errno=RET.PARAMERR,errmsg='参数缺失')
    # 转换新闻分类数据类型
    try:
        category_id = int(category_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR,errmsg='参数类型错误')
    # 读取图片数据
    try:
        image_data = index_image.read()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR,errmsg='参数格式错误')
    # 调用七牛云上传图片
    try:
        image_name = storage(image_data)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR,errmsg='上传图片失败')
    # 保存新闻数据
    news = News()
    news.category_id = category_id
    news.user_id = user.id
    news.source = '个人发布'
    news.title = title
    news.digest = digest

    # news.index_image_url = index_image
    # 新闻图片应该存储的是图片的绝对路径,让新闻图片和新闻内容是一个整体。
    news.index_image_url = constants.QINIU_DOMIN_PREFIX + image_name
    news.content = content
    news.status = 1
    # 提交数据
    try:
        db.session.add(news)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR,errmsg='保存数据失败')
    # 返回结果
    return jsonify(errno=RET.OK,errmsg='OK')
