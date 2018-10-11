from flask import request,jsonify,current_app,make_response,session

from . import passport_blue
# 导入自定义的状态码
from info.utils.response_code import RET
# 导入生成图片验证码的工具
from info.utils.captcha.captcha import captcha
# 导入redis实例,常量文件
from info import redis_store,constants,db
# 导入正则
import re,random
# 导入云通讯
from info.libs.yuntongxun import sms
# 导入模型类User
from info.models import User

from info.utils.send_email import SendEmail

from  datetime import datetime
"""
生成图片验证码
发送短信
注册
登录
退出

"""
@passport_blue.route("/image_code")
def generate_image_code():
    """
    生成图片验证码
    uuid：全局唯一的标识符，redis.setex('ImageCode_' + uuid )
    1、获取前端生成的uuid
    request.args.get("image_code_id")
    2、判断参数是否存在，如果不存在直接return
    3、使用工具captcha生成图片验证码,name,text,image
    4、保存图片验证码的text文本，redis数据库中
    5、返回图片

    :return:
    """
    # 获取前端传入的图片验证码的编号uuid
    image_code_id = request.args.get('image_code_id')
    # 判断参数是否存在
    if not image_code_id:
        return jsonify(errno=RET.PARAMERR,errmsg='参数缺失')
    # 调用captcha工具，生成图片验证码
    name,text,image = captcha.generate_captcha()
    print(text)
    # 保存图片验证码的文本到redis数据库中
    try:
        redis_store.setex('ImageCode_' + image_code_id,constants.IMAGE_CODE_REDIS_EXPIRES,text)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='保存数据异常')
    else:
        response = make_response(image)
        # 修改默认的响应类型，text/html,
        response.headers['Content-Type'] = 'image/jpg'
        return response


@passport_blue.route("/email_code",methods=['POST'])
def send_email():
    '''
    发送email
    1.获取参数 email， image_code,image_code_id
    2.检查参数完整性
    3.检查email的格式，正则
    4.尝试从Redis中获取验证码
    5.判断获取结果，如果不存在，说明图片验证码过期
    6、删除redis中存储的图片验证码，因为图片验证码无论正确与否，只能比较一次，
    7、比较图片验证码是否正确
    8、构造email随机码，6位数
    9.发送email
    10.返回结果
    
    :return: 
    '''
    # 获取参数
    email = request.json.get('email')
    print(email)
    image_code = request.json.get('image_code')
    image_code_id = request.json.get('image_code_id')
    # 检查参数的完整性
    # if mobile and image_code and image_code_id:
    if not all([email, image_code, image_code_id]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数不完整')
        # 使用正则校验手机号格式
    if not re.match('^([a-z0-9_\.-]+)@([\da-z\.-]+)\.([a-z\.]{2,6})$', email):
        return jsonify(errno=RET.PARAMERR, errmsg='email格式错误')

    # 获取redis中存储的真实图片验证码
    try:
        real_image_code = redis_store.get('ImageCode_' + image_code_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='获取数据失败')
        # 判断获取结果
    if not real_image_code:
        return jsonify(errno=RET.NODATA, errmsg='图片验证码已过期')
        # 删除redis中的图片验证码
    try:
        redis_store.delete('ImageCode_' + image_code_id)
    except Exception as e:
        current_app.logger.error(e)
        # 比较图片验证码是否一致,忽略大小写
    if real_image_code.lower() != image_code.lower():
        return jsonify(errno=RET.DATAERR, errmsg='图片验证码不一致')

    # 判断email是否已注册
    try:
        user = User.query.filter_by(email=email).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询用户数据失败')
    else:
        if user:
            return jsonify(errno=RET.DATAEXIST, errmsg='email已注册')
    # 构造六位数的短信随机数
    sms_code = '%06d' % random.randint(0, 999999)
    print(sms_code)
    # 存入到redis数据库中
    try:
        redis_store.setex('SMSCode_' + email, constants.SMS_CODE_REDIS_EXPIRES, sms_code)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='保存数据异常')
    # 使用email 发送验证码

    try:
        em = SendEmail(email, str(sms_code))
        ret = em.send()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR, errmsg='发送email异常')
    if ret == 1:
        return jsonify(errno=RET.OK, errmsg='发送成功')
    else:
        return jsonify(errno=RET.THIRDERR, errmsg='发送email异常')


@passport_blue.route("/sms_code",methods=['POST'])
def send_sms_code():
    """
    发送短信：web开发：写接口、调接口
    获取参数----检查参数----业务处理----返回结果
    1、获取参数mobile，image_code,image_code_id
    2、检查参数的完整性
    3、检查手机号的格式，正则
    4、尝试从redis中获取真实的图片验证码
    image_code = redis_store.get(imagecode)
    5、判断获取结果，如果不存在，说明图片验证码已过期
    6、删除redis中存储的图片验证码，因为图片验证码无论正确与否，只能比较一次，
    7、比较图片验证码是否正确
    8、构造短信随机码，6位数
    9、使用云通讯发送短信，保存发送结果
    10、返回结果
    :return:
    """
    # 获取参数
    mobile = request.json.get('mobile')
    image_code = request.json.get('image_code')
    image_code_id = request.json.get('image_code_id')
    # 检查参数的完整性
    # if mobile and image_code and image_code_id:
    if not all([mobile,image_code,image_code_id]):
        return jsonify(errno=RET.PARAMERR,errmsg='参数不完整')
    # 使用正则校验手机号格式
    if not re.match(r'1[3456789]\d{9}$',mobile):
        return jsonify(errno=RET.PARAMERR,errmsg='手机号格式错误')
    # 手机号是否注册可以

    # 获取redis中存储的真实图片验证码
    try:
        real_image_code = redis_store.get('ImageCode_' + image_code_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='获取数据失败')
    # 判断获取结果
    if not real_image_code:
        return jsonify(errno=RET.NODATA,errmsg='图片验证码已过期')
    # 删除redis中的图片验证码
    try:
        redis_store.delete('ImageCode_' + image_code_id)
    except Exception as e:
        current_app.logger.error(e)
    # 比较图片验证码是否一致,忽略大小写
    if real_image_code.lower() != image_code.lower():
        return jsonify(errno=RET.DATAERR,errmsg='图片验证码不一致')
    # 判断手机号是否已注册
    try:
        user = User.query.filter_by(mobile=mobile).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询用户数据失败')
    else:
        if user:
            return jsonify(errno=RET.DATAEXIST, errmsg='手机号已注册')

    # 构造六位数的短信随机数
    sms_code = '%06d' % random.randint(0, 999999)
    print(sms_code)
    # 存入到redis数据库中
    try:
        redis_store.setex('SMSCode_' + mobile,constants.SMS_CODE_REDIS_EXPIRES,sms_code)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='保存数据异常')


    # 使用云通讯发送短信
    try:
        ccp = sms.CCP()
        results = ccp.send_template_sms(mobile,[sms_code,constants.SMS_CODE_REDIS_EXPIRES/60],1)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR,errmsg='发送短信异常')
    # 判断发送结果
    if results == 0:
        return jsonify(errno=RET.OK,errmsg='发送成功')
    else:
        return jsonify(errno=RET.THIRDERR,errmsg='发送失败')


@passport_blue.route('/register',methods=['POST'])
def register():
    """
    用户注册
    1、获取参数，mobile，sms_code,password
    2、检查参数完整性
    3、检查手机号的格式
    4、尝试从redis中获取真实的短信验证码
    5、判断获取结果是否存在
    6、先比较短信验证码是否正确
    7、删除redis中存储的短信验证码
    8、构造模型类对象，存储用户信息
    9、提交数据到数据库中
    10、缓存用户信息到redis数据库中
    11、返回结果
    :return:
    """
    # 获取参数
    mobile = request.json.get('mobile')
    email = request.json.get("email")
    sms_code = request.json.get('sms_code')
    password = request.json.get('password')
    # 检查参数的完整性
    if not all([email,sms_code,password]):
        return jsonify(errno=RET.PARAMERR,errmsg='参数缺失')
    # 使用正则校验手机号格式
    # if not re.match(r'1[3456789]\d{9}$', mobile):
    #     return jsonify(errno=RET.PARAMERR, errmsg='手机号格式错误')
    if not re.match('^([a-z0-9_\.-]+)@([\da-z\.-]+)\.([a-z\.]{2,6})$', email):
        return jsonify(errno=RET.PARAMERR, errmsg='email格式错误')
    # 从redis中获取真实的短信验证码
    try:
        real_sms_code = redis_store.get('SMSCode_' + email)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='获取数据失败')
    # 判断获取结果是否存在
    if not real_sms_code:
        return jsonify(errno=RET.NODATA,errmsg='数据已过期')
    # 比较短信验证码是否一致
    if real_sms_code != str(sms_code):
        return jsonify(errno=RET.DATAERR,errmsg='短信验证码不一致')
    # 删除短信验证码
    try:
        redis_store.delete('SMSCode_' + email)
    except Exception as e:
        current_app.logger.error(e)
    # 判断手机号是否已注册
    try:
        user = User.query.filter_by(email=email).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='查询用户数据失败')
    else:
        if user:
            return jsonify(errno=RET.DATAEXIST,errmsg='邮箱已注册')
    # 保存用户信息
    user = User()
    # user.mobile = '18772845363'
    user.email = email
    user.nick_name = email
    # 实际上调用了模型类中的password方法，实现了密码加密存储，generate_password_hash
    user.password = password
    # 提交数据到mysql
    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR,errmsg='保存数据失败')
    # 缓存用户信息
    session['user_id'] = user.id
    session['email'] = email
    session['nick_name'] = email
    # 返回结果
    return jsonify(errno=RET.OK,errmsg='OK')


@passport_blue.route("/login",methods=['post'])
def login():
    '''
    1.接受参数 email ,password
    2.参数验证
    3.数据库查询用户
    4.校验密码
    5.缓存用户信息
    :return: 
    '''
    email = request.json.get('email')
    password = request.json.get('password')
    if not all([email,password]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数缺失')
    # 检查手机号的格式
    if not re.match('^([a-z0-9_\.-]+)@([\da-z\.-]+)\.([a-z\.]{2,6})$', email):
        return jsonify(errno=RET.PARAMERR, errmsg='email格式错误')
    # 根据手机号查询mysql数据库
    try:
        user = User.query.filter_by(email=email).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询数据库失败')
    # 判断查询结果是否存在
    # if not user:
    #     return jsonify(errno=RET.NODATA,errmsg='用户未注册')
    # # 判断密码是否正确
    # if not user.check_password(password):
    #     return jsonify(errno=RET.PWDERR,errmsg='密码错误')
    # 如果用户为None，或者密码错误
    if user is None or not user.check_password(password):
        return jsonify(errno=RET.PWDERR, errmsg='用户名或密码错误')
    # 保存用户的登录时间
    user.last_login = datetime.now()
    # 提交数据到数据库中
    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg='保存数据失败')
    # 缓存用户信息
    session['user_id'] = user.id
    session['email'] = email
    session['nick_name'] = user.nick_name
    # session['user'] = user
    # 返回结果
    return jsonify(errno=RET.OK, errmsg='登录成功')


@passport_blue.route('/logout')
def logout():
    """退出登录"""
    # 本质是清除用户在服务器缓存的用户信息
    session.pop('user_id',None)
    session.pop('mobile',None)
    session.pop('nick_name',None)
    return jsonify(errno=RET.OK,errmsg='OK')





