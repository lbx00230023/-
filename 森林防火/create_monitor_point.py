from app import app, db
from models import MonitorPoint, User, FireThreshold

def create_default_monitor_point():
    """创建默认监测点和阈值设置"""
    with app.app_context():
        # 检查是否已有监测点
        if MonitorPoint.query.count() == 0:
            # 创建默认监测点
            default_point = MonitorPoint(
                name='默认监测点',
                latitude=35.0,
                longitude=116.0,
                active=True
            )
            db.session.add(default_point)
            print("创建默认监测点成功")
            
        # 检查是否已有阈值设置
        if FireThreshold.query.count() == 0:
            # 创建默认阈值设置
            default_threshold = FireThreshold(
                wind_speed_threshold=10.0,
                temperature_threshold=30.0,
                humidity_threshold=30.0,
                updated_by=1  # 默认管理员ID
            )
            db.session.add(default_threshold)
            print("创建默认阈值设置成功")
            
        db.session.commit()
        print("默认数据初始化完成")

if __name__ == "__main__":
    create_default_monitor_point() 