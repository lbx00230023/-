from app import app, bcrypt, db
from models import User, MonitorPoint, MonitorRecord, FireThreshold
from datetime import datetime, timedelta
import random
import os

def init_database():
    with app.app_context():
        print("开始初始化数据库...")
        
        # 强制删除旧的数据库文件
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'forest_fire.db')
        if os.path.exists(db_path):
            try:
                os.remove(db_path)
                print(f"已删除旧数据库文件: {db_path}")
            except Exception as e:
                print(f"无法删除数据库文件: {e}")
        
        # 创建所有表
        db.create_all()
        print("已创建数据库表")
        
        print("创建初始管理员用户...")
        # 创建管理员账户
        admin_password = bcrypt.generate_password_hash("111").decode('utf-8')
        admin = User(
            username="admit",
            password=admin_password,
            email="admin@example.com",
            role="admin"
        )
        db.session.add(admin)
        
        # 创建普通用户账户
        user_password = bcrypt.generate_password_hash("user123").decode('utf-8')
        user = User(
            username="user",
            password=user_password,
            email="user@example.com",
            role="user"
        )
        db.session.add(user)
        db.session.commit()
        print("用户创建成功")
        
        # 创建监测点
        print("创建初始监测点...")
        # 创建几个监测点
        monitor_points = [
            MonitorPoint(name="林区监测点A", latitude=36.5, longitude=117.2),
            MonitorPoint(name="林区监测点B", latitude=36.7, longitude=117.4),
            MonitorPoint(name="林区监测点C", latitude=36.3, longitude=117.3),
            MonitorPoint(name="林区监测点D", latitude=36.6, longitude=117.5)
        ]
        db.session.add_all(monitor_points)
        db.session.commit()
        print("监测点创建成功")
    
        # 为每个监测点添加历史数据
        print("添加监测数据...")
        monitor_points = MonitorPoint.query.all()
        now = datetime.utcnow()
        
        for point in monitor_points:
            # 为每个点添加10条历史记录
            for i in range(10):
                record_time = now - timedelta(hours=i*6)
                record = MonitorRecord(
                    monitor_point_id=point.id,
                    wind_speed=round(random.uniform(5, 15), 1),
                    temperature=round(random.uniform(20, 35), 1),
                    humidity=round(random.uniform(30, 80), 1),
                    timestamp=record_time
                )
                db.session.add(record)
        
        db.session.commit()
        print("监测数据添加成功")
    
        # 创建阈值设置
        print("创建初始阈值设置...")
        # 创建阈值设置
        threshold = FireThreshold(
            wind_speed_threshold=10.0,
            temperature_threshold=30.0,
            humidity_threshold=30.0,
            updated_by=1  # 管理员ID
        )
        db.session.add(threshold)
        db.session.commit()
        print("阈值设置创建成功")
        
        # 验证用户创建
        users = User.query.all()
        print("\n数据库中的用户:")
        for user in users:
            print(f"ID: {user.id}, 用户名: {user.username}, 角色: {user.role}")
        
        print("\n数据库初始化完成!")

if __name__ == "__main__":
    init_database() 