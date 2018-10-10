from redis import StrictRedis
class Config:
    DEBUG = None
    # 设置密钥
    SECRET_KEY = 'cYaRoiV/yG7qq6L2/nPHKOgqGspSjkBDJ02iWrhQFJaz8002cI3GbjsZnP5tEV3vad8='

    # 配置mysql数据库的连接信息
    SQLALCHEMY_DATABASE_URI = 'mysql://root:root@localhost/info14'
    SQLALCHEMY_TRACK_MODIFICATIONS = False


    # 配置redis连接信息
    REDIS_HOST = '127.0.0.1'
    REDIS_PORT = 6379

    # 配置状态保持中的session信息，存储在redis数据库中
    SESSION_TYPE = 'redis'
    SESSION_REDIS = StrictRedis(host=REDIS_HOST,port=REDIS_PORT) # session连接的redis数据库实例

    SESSION_USE_SIGNER = True # session签名
    PERMANENT_SESSION_LIFETIME = 86400 # session有效期

# 实现开发模式下的配置信息
class DevelopmentConfig(Config):
    DEBUG = True


# 实现生产模式下的配置信息
class ProductionConfig(Config):
    DEBUG = False


# 定义字典，实现配置对象的映射
config_dict = {
    'development':DevelopmentConfig,
    'production':ProductionConfig
}
