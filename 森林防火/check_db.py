from app import app
from models import User, db

with app.app_context():
    users = User.query.all()
    print("数据库中的用户信息:")
    print("-" * 50)
    print("| ID | 用户名 | 邮箱 | 角色 | 密码哈希(前20字符) |")
    print("-" * 50)
    for user in users:
        print(f"| {user.id} | {user.username} | {user.email} | {user.role} | {user.password[:20]}... |")
    print("-" * 50) 