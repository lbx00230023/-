from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import MonitorPoint, MonitorRecord, FireThreshold, FireData, db
from routes.user_routes import admin_required
from datetime import datetime
from fire_prediction import FirePredictor

fire_routes = Blueprint('fire', __name__, url_prefix='/api/fire')

# 火灾预测相关路由
@fire_routes.route('/predict', methods=['GET'])
def predict_fire_risk():
    """预测所有监测点的火灾风险"""
    # 调用分析函数分析所有监测点的最新数据
    results = FirePredictor.analyze_monitor_data()
    
    return jsonify(results), 200

@fire_routes.route('/predict/<int:point_id>', methods=['GET'])
def predict_fire_risk_for_point(point_id):
    """预测特定监测点的火灾风险"""
    # 检查监测点是否存在
    point = MonitorPoint.query.get(point_id)
    if not point:
        return jsonify({'message': '监测点不存在'}), 404
    
    # 调用分析函数分析指定监测点的最新数据
    results = FirePredictor.analyze_monitor_data(point_id)
    
    if not results:
        return jsonify({'message': '无可用的监测数据'}), 404
    
    return jsonify(results[0]), 200

@fire_routes.route('/predict/custom', methods=['POST'])
def predict_custom_data():
    """使用自定义数据进行火灾风险预测"""
    data = request.get_json()
    
    # 检查必填字段
    if not data or not all(k in data for k in ('wind_speed', 'temperature', 'humidity')):
        return jsonify({'message': '缺少必填字段'}), 400
    
    try:
        # 尝试转换数据类型
        wind_speed = float(data['wind_speed'])
        temperature = float(data['temperature'])
        humidity = float(data['humidity'])
    except (ValueError, TypeError):
        return jsonify({'message': '输入数据格式错误，请确保风速、温度和湿度为数值类型'}), 400
    
    # 获取阈值设置
    threshold = FireThreshold.query.order_by(FireThreshold.id.desc()).first()
    
    # 预测风险等级
    try:
        risk_level = FirePredictor.predict_risk(
            wind_speed, 
            temperature, 
            humidity,
            threshold
        )
        
        # 预测可能火灾面积
        predicted_area = FirePredictor.predict_fire_area(
            wind_speed, 
            temperature, 
            humidity, 
            risk_level
        )
        
        result = {
            'wind_speed': wind_speed,
            'temperature': temperature,
            'humidity': humidity,
            'risk_level': risk_level,
            'predicted_area': predicted_area
        }
        
        return jsonify(result), 200
    except Exception as e:
        print(f"预测过程中发生错误: {str(e)}")
        return jsonify({'message': f'预测过程中发生错误: {str(e)}'}), 500

@fire_routes.route('/save-prediction', methods=['POST'])
def save_fire_prediction():
    """保存火灾预测结果"""
    # 移除JWT认证，允许未登录用户保存
    data = request.get_json()
    
    # 检查必填字段
    if not data or not all(k in data for k in ('wind_speed', 'temperature', 
                                             'humidity', 'risk_level', 'predicted_area')):
        return jsonify({'message': '缺少必填字段'}), 400
    
    try:
        # 尝试转换数据类型
        wind_speed = float(data['wind_speed'])
        temperature = float(data['temperature'])
        humidity = float(data['humidity'])
        predicted_area = float(data['predicted_area'])
    except (ValueError, TypeError):
        return jsonify({'message': '输入数据格式错误，请确保风速、温度、湿度和预测面积为数值类型'}), 400
    
    # 创建新的火灾数据记录
    new_fire_data = FireData(
        monitor_point_id=data.get('monitor_point_id', 1),  # 如果没有指定监测点，使用默认值1
        wind_speed=wind_speed,
        temperature=temperature,
        humidity=humidity,
        risk_level=data['risk_level'],
        predicted_area=predicted_area,
        timestamp=datetime.utcnow(),
        latitude=float(data.get('latitude', 35.0)),  # 使用默认值或提供的值
        longitude=float(data.get('longitude', 116.0))  # 使用默认值或提供的值
    )
    
    # 保存到数据库
    db.session.add(new_fire_data)
    db.session.commit()
    
    return jsonify({'message': '火灾预测数据保存成功', 'fire_data': new_fire_data.to_dict()}), 201

# 火灾阈值相关路由
@fire_routes.route('/threshold', methods=['GET'])
def get_fire_threshold():
    """获取当前火灾阈值设置"""
    threshold = FireThreshold.query.order_by(FireThreshold.id.desc()).first()
    
    if not threshold:
        # 返回默认阈值
        return jsonify({
            'wind_speed_threshold': 10.0,
            'temperature_threshold': 30.0,
            'humidity_threshold': 30.0
        }), 200
    
    return jsonify(threshold.to_dict()), 200

@fire_routes.route('/threshold', methods=['POST'])
def set_fire_threshold():
    """设置火灾阈值（允许非管理员）"""
    # 移除admin_required认证，改为普通认证
    data = request.get_json()
    
    # 检查必填字段
    if not data or not all(k in data for k in ('wind_speed_threshold', 'temperature_threshold', 'humidity_threshold')):
        return jsonify({'message': '缺少必填字段'}), 400
    
    try:
        # 尝试转换数据类型
        wind_speed_threshold = float(data['wind_speed_threshold'])
        temperature_threshold = float(data['temperature_threshold'])
        humidity_threshold = float(data['humidity_threshold'])
    except (ValueError, TypeError):
        return jsonify({'message': '输入数据格式错误，请确保阈值为数值类型'}), 400
    
    # 创建新的阈值设置
    new_threshold = FireThreshold(
        wind_speed_threshold=wind_speed_threshold,
        temperature_threshold=temperature_threshold,
        humidity_threshold=humidity_threshold,
        updated_by=1  # 使用默认用户ID
    )
    
    # 保存到数据库
    db.session.add(new_threshold)
    db.session.commit()
    
    return jsonify({'message': '火灾阈值设置更新成功', 'threshold': new_threshold.to_dict()}), 201

# 火灾数据记录相关路由
@fire_routes.route('/data', methods=['GET'])
@jwt_required()
def get_fire_data():
    """获取火灾数据记录列表，可按风险等级过滤"""
    # 获取查询参数
    risk_level = request.args.get('risk_level')
    limit = request.args.get('limit', 100, type=int)
    
    # 构建查询
    query = FireData.query
    
    # 按风险等级过滤
    if risk_level:
        query = query.filter_by(risk_level=risk_level)
    
    # 按时间排序并限制返回数量
    fire_data = query.order_by(FireData.timestamp.desc()).limit(limit).all()
    
    return jsonify([data.to_dict() for data in fire_data]), 200

@fire_routes.route('/data/<int:data_id>', methods=['GET'])
@jwt_required()
def get_fire_data_detail(data_id):
    """获取特定火灾数据记录详情"""
    fire_data = FireData.query.get(data_id)
    if not fire_data:
        return jsonify({'message': '火灾数据记录不存在'}), 404
    
    return jsonify(fire_data.to_dict()), 200

@fire_routes.route('/data/<int:data_id>', methods=['DELETE'])
@admin_required
def delete_fire_data(data_id):
    """删除火灾数据记录（仅管理员）"""
    fire_data = FireData.query.get(data_id)
    if not fire_data:
        return jsonify({'message': '火灾数据记录不存在'}), 404
    
    # 删除火灾数据记录
    db.session.delete(fire_data)
    db.session.commit()
    
    return jsonify({'message': '火灾数据记录删除成功'}), 200 