from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import User, db
from app import bcrypt

user_routes = Blueprint('user', __name__, url_prefix='/api/users')

# 检查管理员身份的装饰器函数
def admin_required(fn):
    @jwt_required()
    def wrapper(*args, **kwargs):
        # 获取当前用户身份
        current_user = get_jwt_identity()
        
        # 检查是否是管理员
        if not current_user or 'role' not in current_user or current_user['role'] != 'admin':
            return jsonify({'message': '需要管理员权限'}), 403
        return fn(*args, **kwargs)
    wrapper.__name__ = fn.__name__
    return wrapper

# 获取所有用户 - 移除JWT认证，便于调试
@user_routes.route('/', methods=['GET'])
def get_all_users():
    """获取所有用户列表（所有人都可以访问）"""
    users = User.query.all()
    return jsonify([user.to_dict() for user in users]), 200

@user_routes.route('/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """获取特定用户详情（所有人都可以访问）"""
    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': '用户不存在'}), 404
    return jsonify(user.to_dict()), 200

@user_routes.route('/', methods=['POST'])
def create_user():
    """创建新用户（所有人都可以创建）"""
    data = request.get_json()
    
    # 检查必填字段
    if not data or not all(k in data for k in ('username', 'password', 'email')):
        return jsonify({'message': '缺少必填字段'}), 400
    
    # 设置默认角色
    role = data.get('role', 'user')
    if role not in ['user', 'admin']:
        role = 'user'  # 如果提供了无效角色，默认为普通用户
    
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
        role=role
    )
    
    # 保存到数据库
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({'message': '用户创建成功', 'user': new_user.to_dict()}), 201

@user_routes.route('/<int:user_id>', methods=['PUT'])
@jwt_required()
def update_user(user_id):
    """更新用户信息（需要JWT认证）"""
    current_user = get_jwt_identity()
    
    # 检查权限（只能修改自己或管理员可以修改任何人）
    if current_user.get('id') != user_id and current_user.get('role') != 'admin':
        return jsonify({'message': '没有权限修改此用户'}), 403
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': '用户不存在'}), 404
    
    data = request.get_json()
    if not data:
        return jsonify({'message': '无效的请求数据'}), 400
    
    # 更新用户名
    if 'username' in data and data['username'] != user.username:
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'message': '用户名已存在'}), 400
        user.username = data['username']
    
    # 更新邮箱
    if 'email' in data and data['email'] != user.email:
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'message': '邮箱已注册'}), 400
        user.email = data['email']
    
    # 更新密码
    if 'password' in data and data['password']:
        user.password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    
    # 更新角色（仅管理员可以）
    if 'role' in data and current_user.get('role') == 'admin':
        if data['role'] not in ['user', 'admin']:
            return jsonify({'message': '无效的角色'}), 400
        user.role = data['role']
    
    # 保存更改
    db.session.commit()
    
    return jsonify({'message': '用户更新成功', 'user': user.to_dict()}), 200

@user_routes.route('/<int:user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(user_id):
    """删除用户（需要JWT认证）"""
    current_user = get_jwt_identity()
    
    # 检查权限（只能删除自己或管理员可以删除任何人，但管理员不能删除自己）
    if current_user.get('id') != user_id and current_user.get('role') != 'admin':
        return jsonify({'message': '没有权限删除此用户'}), 403
    
    if current_user.get('id') == user_id and current_user.get('role') == 'admin':
        return jsonify({'message': '不能删除当前登录的管理员账号'}), 400
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': '用户不存在'}), 404
    
    # 删除用户
    db.session.delete(user)
    db.session.commit()
    
    return jsonify({'message': '用户删除成功'}), 200

@user_routes.route('/set-admin/<int:user_id>', methods=['PUT'])
@jwt_required()
def set_admin(user_id):
    """将用户设置为管理员（需要JWT认证，仅管理员可操作）"""
    current_user = get_jwt_identity()
    
    # 检查权限
    if current_user.get('role') != 'admin':
        return jsonify({'message': '需要管理员权限'}), 403
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': '用户不存在'}), 404
    
    # 已经是管理员
    if user.role == 'admin':
        return jsonify({'message': '该用户已经是管理员'}), 400
    
    # 设置为管理员
    user.role = 'admin'
    db.session.commit()
    
    return jsonify({'message': '用户已被设置为管理员', 'user': user.to_dict()}), 200

@user_routes.route('/remove-admin/<int:user_id>', methods=['PUT'])
@jwt_required()
def remove_admin(user_id):
    """移除用户的管理员权限（需要JWT认证，仅管理员可操作）"""
    current_user = get_jwt_identity()
    
    # 检查权限
    if current_user.get('role') != 'admin':
        return jsonify({'message': '需要管理员权限'}), 403
    
    # 不允许移除自己的管理员权限
    if current_user.get('id') == user_id:
        return jsonify({'message': '不能移除自己的管理员权限'}), 400
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': '用户不存在'}), 404
    
    # 不是管理员
    if user.role != 'admin':
        return jsonify({'message': '该用户不是管理员'}), 400
    
    # 移除管理员权限
    user.role = 'user'
    db.session.commit()
    
    return jsonify({'message': '已移除用户的管理员权限', 'user': user.to_dict()}), 200 