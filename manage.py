from flask_migrate import MigrateCommand,Migrate

# 使用管理器
from flask_script import Manager
# 导入工厂函数
from info import create_app,db,models

# 调用__init__文件中的工厂函数，获取app
app = create_app('development')

manage = Manager(app)
Migrate(app,db)
manage.add_command('db',MigrateCommand)


if __name__ == '__main__':
    print(app.url_map)
    manage.run()
