from app import app, bcrypt, db
from models import User

def create_admin():
    with app.app_context():
        try:
            # 创建表(如果不存在)
            db.create_all()
            print("确保数据库表已创建")
            
            # 获取所有用户
            all_users = User.query.all()
            print(f"当前数据库中共有 {len(all_users)} 个用户")
            
            # 检查是否已有指定用户名的用户
            admin = User.query.filter_by(username="admit").first()
            if admin:
                print(f"用户 'admit' 已存在 (ID: {admin.id})")
                # 更新密码
                admin.password = bcrypt.generate_password_hash("111").decode('utf-8')
                admin.role = "admin"
                db.session.commit()
                print("已更新用户密码和角色")
            else:
                # 创建新的管理员用户
                admin_password = bcrypt.generate_password_hash("111").decode('utf-8')
                new_admin = User(
                    username="admit",
                    password=admin_password,
                    email="admin@example.com",
                    role="admin"
                )
                db.session.add(new_admin)
                db.session.commit()
                print(f"管理员用户创建成功 (ID: {new_admin.id})")
            
            # 显示所有用户，包括属性调试
            users = User.query.all()
            print("\n数据库中的所有用户:")
            print("-" * 70)
            print("| ID | 用户名 | 邮箱 | 角色 | 密码哈希(前20字符) |")
            print("-" * 70)
            for user in users:
                print(f"| {user.id} | {user.username} | {user.email} | {user.role} | {user.password[:20]}... |")
                # 尝试再次查询用户对象
                queried_user = User.query.get(user.id)
                if queried_user:
                    print(f"  - 可以通过ID {user.id} 查询到用户")
                else:
                    print(f"  - 无法通过ID {user.id} 查询到用户！")
            print("-" * 70)
            
            # 特别检查 admit 用户
            special_check = User.query.filter_by(username="admit").first()
            if special_check:
                print(f"特别检查: 'admit' 用户存在 (ID: {special_check.id})")
            else:
                print("特别检查: 'admit' 用户不存在")
                
        except Exception as e:
            print(f"发生错误: {e}")

if __name__ == "__main__":
    create_admin() 