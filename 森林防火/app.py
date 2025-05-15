from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt
from datetime import timedelta
import os
from dotenv import load_dotenv
from models import db, User, MonitorPoint, FireData, FireThreshold

# 加载环境变量
load_dotenv()

# 初始化Flask应用
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev_secret_key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI', 'sqlite:///forest_fire.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'jwt_secret_key')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
# 配置JWT错误处理
app.config['JWT_ERROR_MESSAGE_KEY'] = 'message'
app.config['PROPAGATE_EXCEPTIONS'] = True  # 允许异常传播

# 跨域支持
CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

# 初始化数据库
db.init_app(app)

# 初始化Bcrypt
bcrypt = Bcrypt(app)

# 初始化JWT
jwt = JWTManager(app)

# 主页路由
@app.route('/')
def index():
    return render_template('index.html')

# 错误处理
@app.errorhandler(404)
def not_found(error):
    return jsonify({'message': 'Not found'}), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({'message': 'Server error'}), 500

# JWT错误处理
@jwt.unauthorized_loader
def unauthorized_callback(callback):
    return jsonify({'message': '未授权访问，请先登录'}), 401

@jwt.invalid_token_loader
def invalid_token_callback(callback):
    return jsonify({'message': '无效的认证令牌'}), 401

@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return jsonify({'message': '认证令牌已过期，请重新登录'}), 401

# 导入并注册蓝图
def register_blueprints(app):
    from routes.auth_routes import auth_routes
    from routes.user_routes import user_routes
    from routes.monitor_routes import monitor_routes
    from routes.fire_routes import fire_routes
    from routes.stat_routes import stat_routes
    
    app.register_blueprint(auth_routes)
    app.register_blueprint(user_routes)
    app.register_blueprint(monitor_routes)
    app.register_blueprint(fire_routes)
    app.register_blueprint(stat_routes)
    
    # 创建数据库表
    with app.app_context():
        db.create_all()
        
        # 检查是否已有用户，如果没有则创建默认管理员
        if User.query.count() == 0:
            admin_password = bcrypt.generate_password_hash('111').decode('utf-8')
            admin_user = User(
                username='admin',
                password=admin_password,
                email='admin@example.com',
                role='admin'
            )
            db.session.add(admin_user)
            db.session.commit()
            print("创建默认管理员账号: admin/111")

if __name__ == '__main__':
    # 注册蓝图
    register_blueprints(app)
    # 运行应用
    app.run(debug=True) 