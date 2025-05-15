from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import MonitorPoint, MonitorRecord, db
from routes.user_routes import admin_required
from datetime import datetime

monitor_routes = Blueprint('monitor', __name__, url_prefix='/api/monitor')

# 监测点相关路由
@monitor_routes.route('/points', methods=['GET'])
def get_all_monitor_points():
    """获取所有监测点"""
    monitor_points = MonitorPoint.query.all()
    return jsonify([point.to_dict() for point in monitor_points]), 200

@monitor_routes.route('/points/<int:point_id>', methods=['GET'])
def get_monitor_point(point_id):
    """获取特定监测点详情"""
    point = MonitorPoint.query.get(point_id)
    if not point:
        return jsonify({'message': '监测点不存在'}), 404
    return jsonify(point.to_dict()), 200

@monitor_routes.route('/points', methods=['POST'])
def create_monitor_point():
    """创建新监测点（所有用户都可以）"""
    data = request.get_json()
    
    # 检查必填字段
    if not data or not all(k in data for k in ('name', 'latitude', 'longitude')):
        return jsonify({'message': '缺少必填字段'}), 400
    
    try:
        # 尝试转换数据类型
        latitude = float(data['latitude'])
        longitude = float(data['longitude'])
    except (ValueError, TypeError):
        return jsonify({'message': '输入数据格式错误，请确保经纬度为数值类型'}), 400
    
    # 检查监测点名称是否已存在
    if MonitorPoint.query.filter_by(name=data['name']).first():
        return jsonify({'message': '监测点名称已存在'}), 400
    
    # 创建新监测点
    new_point = MonitorPoint(
        name=data['name'],
        latitude=latitude,
        longitude=longitude,
        active=data.get('active', True)
    )
    
    # 保存到数据库
    db.session.add(new_point)
    db.session.commit()
    
    return jsonify({'message': '监测点创建成功', 'monitor_point': new_point.to_dict()}), 201

@monitor_routes.route('/points/<int:point_id>', methods=['PUT'])
@admin_required
def update_monitor_point(point_id):
    """更新监测点信息（仅管理员）"""
    point = MonitorPoint.query.get(point_id)
    if not point:
        return jsonify({'message': '监测点不存在'}), 404
    
    data = request.get_json()
    if not data:
        return jsonify({'message': '无效的请求数据'}), 400
    
    # 更新监测点名称
    if 'name' in data and data['name'] != point.name:
        if MonitorPoint.query.filter_by(name=data['name']).first():
            return jsonify({'message': '监测点名称已存在'}), 400
        point.name = data['name']
    
    # 更新经纬度
    if 'latitude' in data:
        point.latitude = data['latitude']
    if 'longitude' in data:
        point.longitude = data['longitude']
    
    # 更新活动状态
    if 'active' in data:
        point.active = data['active']
    
    # 保存更改
    db.session.commit()
    
    return jsonify({'message': '监测点更新成功', 'monitor_point': point.to_dict()}), 200

@monitor_routes.route('/points/<int:point_id>', methods=['DELETE'])
@admin_required
def delete_monitor_point(point_id):
    """删除监测点（仅管理员）"""
    point = MonitorPoint.query.get(point_id)
    if not point:
        return jsonify({'message': '监测点不存在'}), 404
    
    # 删除监测点
    db.session.delete(point)
    db.session.commit()
    
    return jsonify({'message': '监测点删除成功'}), 200

# 监测数据相关路由
@monitor_routes.route('/records', methods=['GET'])
@jwt_required()
def get_all_monitor_records():
    """获取所有监测记录或按监测点过滤"""
    # 获取查询参数
    point_id = request.args.get('point_id', type=int)
    limit = request.args.get('limit', 100, type=int)
    
    # 构建查询
    query = MonitorRecord.query
    
    # 按监测点过滤
    if point_id:
        query = query.filter_by(monitor_point_id=point_id)
    
    # 按时间排序并限制返回数量
    records = query.order_by(MonitorRecord.timestamp.desc()).limit(limit).all()
    
    return jsonify([record.to_dict() for record in records]), 200

@monitor_routes.route('/records/<int:record_id>', methods=['GET'])
@jwt_required()
def get_monitor_record(record_id):
    """获取特定监测记录详情"""
    record = MonitorRecord.query.get(record_id)
    if not record:
        return jsonify({'message': '监测记录不存在'}), 404
    return jsonify(record.to_dict()), 200

@monitor_routes.route('/records', methods=['POST'])
@jwt_required()
def create_monitor_record():
    """创建新监测记录"""
    data = request.get_json()
    
    # 检查必填字段
    if not data or not all(k in data for k in ('monitor_point_id', 'wind_speed', 'temperature', 'humidity')):
        return jsonify({'message': '缺少必填字段'}), 400
    
    # 检查监测点是否存在
    monitor_point = MonitorPoint.query.get(data['monitor_point_id'])
    if not monitor_point:
        return jsonify({'message': '监测点不存在'}), 404
    
    # 创建新监测记录
    new_record = MonitorRecord(
        monitor_point_id=data['monitor_point_id'],
        wind_speed=data['wind_speed'],
        temperature=data['temperature'],
        humidity=data['humidity'],
        timestamp=datetime.utcnow()
    )
    
    # 保存到数据库
    db.session.add(new_record)
    db.session.commit()
    
    return jsonify({'message': '监测记录创建成功', 'record': new_record.to_dict()}), 201

@monitor_routes.route('/records/<int:record_id>', methods=['PUT'])
@admin_required
def update_monitor_record(record_id):
    """更新监测记录（仅管理员）"""
    record = MonitorRecord.query.get(record_id)
    if not record:
        return jsonify({'message': '监测记录不存在'}), 404
    
    data = request.get_json()
    if not data:
        return jsonify({'message': '无效的请求数据'}), 400
    
    # 更新数据
    if 'wind_speed' in data:
        record.wind_speed = data['wind_speed']
    if 'temperature' in data:
        record.temperature = data['temperature']
    if 'humidity' in data:
        record.humidity = data['humidity']
    if 'monitor_point_id' in data:
        # 检查监测点是否存在
        if not MonitorPoint.query.get(data['monitor_point_id']):
            return jsonify({'message': '监测点不存在'}), 404
        record.monitor_point_id = data['monitor_point_id']
    
    # 保存更改
    db.session.commit()
    
    return jsonify({'message': '监测记录更新成功', 'record': record.to_dict()}), 200

@monitor_routes.route('/records/<int:record_id>', methods=['DELETE'])
@admin_required
def delete_monitor_record(record_id):
    """删除监测记录（仅管理员）"""
    record = MonitorRecord.query.get(record_id)
    if not record:
        return jsonify({'message': '监测记录不存在'}), 404
    
    # 删除监测记录
    db.session.delete(record)
    db.session.commit()
    
    return jsonify({'message': '监测记录删除成功'}), 200

@monitor_routes.route('/latest', methods=['GET'])
def get_latest_records():
    """获取每个监测点的最新数据"""
    # 使用子查询获取每个监测点的最新记录
    latest_records_query = db.session.query(
        MonitorRecord.monitor_point_id,
        db.func.max(MonitorRecord.timestamp).label('max_time')
    ).group_by(MonitorRecord.monitor_point_id).subquery('latest_records')
    
    # 获取实际记录
    records = db.session.query(MonitorRecord).join(
        latest_records_query,
        db.and_(
            MonitorRecord.monitor_point_id == latest_records_query.c.monitor_point_id,
            MonitorRecord.timestamp == latest_records_query.c.max_time
        )
    ).all()
    
    return jsonify([record.to_dict() for record in records]), 200 