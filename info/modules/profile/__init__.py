from flask import Blueprint

profile_blue = Blueprint('profile_blue', __name__, url_prefix='/user')

# RESTful：表现层状态转换，开发web项目需要具备的风格特点。
from . import views