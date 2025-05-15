from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from models import User, db
from app import bcrypt

auth_routes = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_routes.route('/register', methods=['POST'])
def register():
    """用户注册"""
    data = request.get_json()
    
    # 检查必填字段
    if not data or not all(k in data for k in ('username', 'password', 'email')):
        return jsonify({'message': '缺少必填字段'}), 400
    
    # 检查用户名是否已存在
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'message': '用户名已存在'}), 400
    
    # 检查邮箱是否已存在
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'message': '邮箱已注册'}), 400
    
    # 创建新用户
    hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    new_user = User(
        username=data['username'],
        password=hashed_password,
        email=data['email'],
        role='user'  # 默认为普通用户
    )
    
    # 保存到数据库
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({'message': '注册成功'}), 201

@auth_routes.route('/login', methods=['POST'])
def login():
    """用户登录"""
    data = request.get_json()
    
    # 检查必填字段
    if not data or not all(k in data for k in ('username', 'password')):
        return jsonify({'message': '请提供用户名和密码'}), 400
    
    # 查找用户
    user = User.query.filter_by(username=data['username']).first()
    
    # 检查用户是否存在及密码是否正确
    if not user or not bcrypt.check_password_hash(user.password, data['password']):
        return jsonify({'message': '用户名或密码错误'}), 401
    
    # 创建访问令牌
    user_claims = {
        'id': user.id,
        'username': user.username,
        'role': user.role
    }
    
    access_token = create_access_token(identity=user_claims)
    
    return jsonify({
        'message': '登录成功',
        'access_token': access_token,
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role
        }
    }), 200

@auth_routes.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """获取当前用户资料"""
    current_user = get_jwt_identity()
    
    # 验证用户ID是否存在
    if not current_user or 'id' not in current_user:
        return jsonify({'message': '无效的用户身份'}), 401
        
    user_id = current_user['id']
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': '用户不存在'}), 404
    
    return jsonify(user.to_dict()), 200

@auth_routes.route('/change-password', methods=['PUT'])
@jwt_required()
def change_password():
    """修改密码"""
    current_user = get_jwt_identity()
    
    # 验证用户ID是否存在
    if not current_user or 'id' not in current_user:
        return jsonify({'message': '无效的用户身份'}), 401
        
    user_id = current_user['id']
    
    data = request.get_json()
    if not data or not all(k in data for k in ('current_password', 'new_password')):
        return jsonify({'message': '请提供当前密码和新密码'}), 400
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': '用户不存在'}), 404
    
    # 验证当前密码
    if not bcrypt.check_password_hash(user.password, data['current_password']):
        return jsonify({'message': '当前密码错误'}), 401
    
    # 更新密码
    user.password = bcrypt.generate_password_hash(data['new_password']).decode('utf-8')
    db.session.commit()
    
    return jsonify({'message': '密码修改成功'}), 200 