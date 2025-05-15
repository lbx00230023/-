from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from models import db, MonitorPoint, FireData
from sqlalchemy import func, and_, extract
from datetime import datetime, timedelta

stat_routes = Blueprint('stats', __name__, url_prefix='/api/stats')

@stat_routes.route('/fire-count', methods=['GET'])
def get_fire_count():
    """获取火灾数量统计"""
    # 移除JWT认证，允许未登录用户访问
    # 获取查询参数：时间范围
    days = request.args.get('days', 30, type=int)
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # 按风险等级分组统计
    result = db.session.query(
        FireData.risk_level,
        func.count(FireData.id).label('count')
    ).filter(
        FireData.timestamp >= start_date
    ).group_by(
        FireData.risk_level
    ).all()
    
    # 格式化结果
    stats = {
        'total': 0,
        'by_risk': {}
    }
    
    for risk_level, count in result:
        stats['by_risk'][risk_level] = count
        stats['total'] += count
    
    return jsonify(stats), 200

@stat_routes.route('/monthly-trend', methods=['GET'])
@jwt_required()
def get_monthly_trend():
    """获取月度火灾趋势"""
    # 获取当前年份
    year = request.args.get('year', datetime.utcnow().year, type=int)
    
    # 按月统计火灾记录
    result = db.session.query(
        extract('month', FireData.timestamp).label('month'),
        func.count(FireData.id).label('count')
    ).filter(
        extract('year', FireData.timestamp) == year
    ).group_by(
        extract('month', FireData.timestamp)
    ).all()
    
    # 格式化结果
    months = [0] * 12  # 初始化每月数据为0
    for month, count in result:
        months[int(month) - 1] = count
    
    return jsonify({
        'year': year,
        'monthly_counts': months
    }), 200

@stat_routes.route('/risk-area-distribution', methods=['GET'])
@jwt_required()
def get_risk_area_distribution():
    """获取风险等级和预测面积分布"""
    # 获取查询参数
    days = request.args.get('days', 30, type=int)
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # 查询数据
    records = FireData.query.filter(
        FireData.timestamp >= start_date,
        FireData.risk_level != 'low'  # 排除低风险记录
    ).all()
    
    # 按风险等级分组
    distribution = {
        'medium': {'count': 0, 'total_area': 0, 'avg_area': 0},
        'high': {'count': 0, 'total_area': 0, 'avg_area': 0},
        'extreme': {'count': 0, 'total_area': 0, 'avg_area': 0}
    }
    
    for record in records:
        if record.risk_level in distribution:
            distribution[record.risk_level]['count'] += 1
            distribution[record.risk_level]['total_area'] += record.predicted_area or 0
    
    # 计算平均面积
    for level in distribution:
        if distribution[level]['count'] > 0:
            distribution[level]['avg_area'] = round(
                distribution[level]['total_area'] / distribution[level]['count'], 
                2
            )
    
    return jsonify(distribution), 200

@stat_routes.route('/geographic-distribution', methods=['GET'])
@jwt_required()
def get_geographic_distribution():
    """获取地理分布统计"""
    # 获取查询参数
    risk_level = request.args.get('risk_level')
    days = request.args.get('days', 30, type=int)
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # 构建查询
    query = db.session.query(
        FireData.latitude,
        FireData.longitude,
        FireData.risk_level,
        func.count(FireData.id).label('count')
    ).filter(
        FireData.timestamp >= start_date
    )
    
    # 按风险等级过滤
    if risk_level:
        query = query.filter(FireData.risk_level == risk_level)
    
    # 按地理位置分组
    result = query.group_by(
        FireData.latitude,
        FireData.longitude,
        FireData.risk_level
    ).all()
    
    # 格式化结果
    geo_stats = []
    for lat, lon, level, count in result:
        geo_stats.append({
            'latitude': lat,
            'longitude': lon,
            'risk_level': level,
            'count': count
        })
    
    return jsonify(geo_stats), 200

@stat_routes.route('/monitor-point-stats', methods=['GET'])
@jwt_required()
def get_monitor_point_stats():
    """获取各监测点统计数据"""
    # 获取查询参数
    days = request.args.get('days', 30, type=int)
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # 查询每个监测点的火灾记录计数
    point_stats = db.session.query(
        MonitorPoint.id,
        MonitorPoint.name,
        MonitorPoint.latitude,
        MonitorPoint.longitude,
        func.count(FireData.id).label('fire_count')
    ).join(
        FireData,
        FireData.monitor_point_id == MonitorPoint.id
    ).filter(
        FireData.timestamp >= start_date
    ).group_by(
        MonitorPoint.id
    ).all()
    
    # 格式化结果
    result = []
    for point_id, name, lat, lon, count in point_stats:
        result.append({
            'monitor_point_id': point_id,
            'name': name,
            'latitude': lat,
            'longitude': lon,
            'fire_count': count
        })
    
    return jsonify(result), 200

@stat_routes.route('/summary', methods=['GET'])
def get_summary_stats():
    """获取总体摘要统计信息"""
    # 移除JWT认证，允许未登录用户访问
    # 获取基本统计数据
    monitor_points_count = MonitorPoint.query.count()
    
    # 计算总火灾记录数
    total_fire_records = FireData.query.count()
    
    # 计算高风险区域数
    high_risk_count = FireData.query.filter(
        FireData.risk_level.in_(['high', 'extreme']),
        FireData.timestamp >= (datetime.utcnow() - timedelta(days=7))
    ).count()
    
    # 计算平均预测火灾面积
    avg_area_result = db.session.query(
        func.avg(FireData.predicted_area)
    ).filter(
        FireData.predicted_area > 0
    ).scalar()
    
    avg_fire_area = round(avg_area_result or 0, 2)
    
    # 获取最近的火灾记录
    recent_fires = FireData.query.order_by(FireData.timestamp.desc()).limit(5).all()
    
    summary = {
        'monitor_points_count': monitor_points_count,
        'total_fire_records': total_fire_records,
        'high_risk_areas_last_week': high_risk_count,
        'avg_fire_area': avg_fire_area,
        'recent_fires': [fire.to_dict() for fire in recent_fires]
    }
    
    return jsonify(summary), 200 