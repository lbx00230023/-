from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# 创建数据库实例
db = SQLAlchemy()

# 用户模型
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    role = db.Column(db.String(20), default='user')  # 'user' 或 'admin'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<User {self.username}>'

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }

# 监测点模型
class MonitorPoint(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    latitude = db.Column(db.Float, nullable=False)  # 纬度
    longitude = db.Column(db.Float, nullable=False)  # 经度
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    active = db.Column(db.Boolean, default=True)
    
    # 一对多关系：一个监测点有多个监测数据
    records = db.relationship('MonitorRecord', backref='monitor_point', lazy=True)

    def __repr__(self):
        return f'<MonitorPoint {self.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'active': self.active
        }

# 监测记录模型
class MonitorRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    monitor_point_id = db.Column(db.Integer, db.ForeignKey('monitor_point.id'), nullable=False)
    wind_speed = db.Column(db.Float, nullable=False)  # 风速 (m/s)
    temperature = db.Column(db.Float, nullable=False)  # 温度 (°C)
    humidity = db.Column(db.Float, nullable=False)  # 湿度 (%)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<MonitorRecord {self.id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'monitor_point_id': self.monitor_point_id,
            'monitor_point_name': self.monitor_point.name,
            'wind_speed': self.wind_speed,
            'temperature': self.temperature,
            'humidity': self.humidity,
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'latitude': self.monitor_point.latitude,
            'longitude': self.monitor_point.longitude
        }

# 火灾阈值设置模型
class FireThreshold(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    wind_speed_threshold = db.Column(db.Float, nullable=False, default=10.0)  # 风速阈值 (m/s)
    temperature_threshold = db.Column(db.Float, nullable=False, default=30.0)  # 温度阈值 (°C)
    humidity_threshold = db.Column(db.Float, nullable=False, default=30.0)  # 湿度阈值 (%)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return f'<FireThreshold {self.id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'wind_speed_threshold': self.wind_speed_threshold,
            'temperature_threshold': self.temperature_threshold,
            'humidity_threshold': self.humidity_threshold,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        }

# 火灾数据模型
class FireData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    monitor_point_id = db.Column(db.Integer, db.ForeignKey('monitor_point.id'), nullable=False)
    wind_speed = db.Column(db.Float, nullable=False)
    temperature = db.Column(db.Float, nullable=False)
    humidity = db.Column(db.Float, nullable=False)
    risk_level = db.Column(db.String(20), nullable=False)  # 'low', 'medium', 'high', 'extreme'
    predicted_area = db.Column(db.Float, nullable=True)  # 预测火灾面积 (平方公里)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f'<FireData {self.id}>'

    def to_dict(self):
        monitor_point = MonitorPoint.query.get(self.monitor_point_id)
        monitor_point_name = monitor_point.name if monitor_point else "未知监测点"
        
        return {
            'id': self.id,
            'monitor_point_id': self.monitor_point_id,
            'monitor_point_name': monitor_point_name,
            'wind_speed': self.wind_speed,
            'temperature': self.temperature,
            'humidity': self.humidity,
            'risk_level': self.risk_level,
            'predicted_area': self.predicted_area,
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'latitude': self.latitude,
            'longitude': self.longitude
        } 