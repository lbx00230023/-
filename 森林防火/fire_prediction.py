import numpy as np
from models import FireThreshold, MonitorRecord, db

class FirePredictor:
    """森林火灾预测模型"""
    
    @staticmethod
    def predict_risk(wind_speed, temperature, humidity, thresholds=None):
        """
        基于监测数据预测火灾风险等级
        
        参数:
        - wind_speed: 风速 (m/s)
        - temperature: 温度 (°C)
        - humidity: 湿度 (%)
        - thresholds: 自定义阈值，若未提供则从数据库获取
        
        返回:
        - risk_level: 风险等级 ('low', 'medium', 'high', 'extreme')
        """
        # 确保数据是浮点型
        try:
            wind_speed = float(wind_speed)
            temperature = float(temperature)
            humidity = float(humidity)
        except (ValueError, TypeError) as e:
            print(f"预测风险时发生类型转换错误: {str(e)}")
            # 如果转换失败，使用默认值
            wind_speed = 10.0
            temperature = 30.0
            humidity = 60.0
        
        # 获取阈值设置
        wind_threshold = 10.0  # 默认值
        temp_threshold = 30.0  # 默认值
        humidity_threshold = 30.0  # 默认值
        
        try:
            if not thresholds:
                threshold = FireThreshold.query.order_by(FireThreshold.id.desc()).first()
                if threshold:
                    wind_threshold = float(threshold.wind_speed_threshold)
                    temp_threshold = float(threshold.temperature_threshold)
                    humidity_threshold = float(threshold.humidity_threshold)
            elif isinstance(thresholds, dict):
                # 如果是字典类型，使用get方法
                wind_threshold = float(thresholds.get('wind_speed_threshold', 10.0))
                temp_threshold = float(thresholds.get('temperature_threshold', 30.0))
                humidity_threshold = float(thresholds.get('humidity_threshold', 30.0))
            else:
                # 如果是对象类型，直接访问属性
                wind_threshold = float(thresholds.wind_speed_threshold)
                temp_threshold = float(thresholds.temperature_threshold)
                humidity_threshold = float(thresholds.humidity_threshold)
        except (ValueError, TypeError, AttributeError) as e:
            print(f"获取阈值时发生错误: {str(e)}")
            # 发生错误时使用默认值，不中断程序
            pass
        
        # 确保阈值不为0，避免除以0错误
        if wind_threshold <= 0:
            wind_threshold = 10.0
        if temp_threshold <= 0:
            temp_threshold = 30.0
        if humidity_threshold <= 0:
            humidity_threshold = 30.0
            
        # 计算风险得分 (0-100)
        try:
            # 风速因子: 风速越大，得分越高
            wind_factor = min(100, (wind_speed / wind_threshold) * 50)
            
            # 温度因子: 温度越高，得分越高
            temp_factor = min(100, (temperature / temp_threshold) * 60)
            
            # 湿度因子: 湿度越低，得分越高
            # 避免除以0错误
            humidity_diff = max(1, 100 - humidity_threshold)
            humidity_factor = min(100, ((100 - humidity) / humidity_diff) * 70)
            
            # 综合得分，加权平均
            risk_score = (wind_factor * 0.3) + (temp_factor * 0.4) + (humidity_factor * 0.3)
        except Exception as e:
            print(f"计算风险得分时发生错误: {str(e)}")
            # 如果计算失败，返回中等风险
            return 'medium'
        
        # 风险等级判定
        if risk_score < 30:
            return 'low'
        elif risk_score < 55:
            return 'medium'
        elif risk_score < 80:
            return 'high'
        else:
            return 'extreme'
    
    @staticmethod
    def predict_fire_area(wind_speed, temperature, humidity, risk_level):
        """
        预测可能的火灾面积 (平方公里)
        
        使用公式: 面积 = 基础面积 * (1 + 风速因子) * 温度因子 * (1 - 湿度因子)
        
        参数:
        - wind_speed: 风速 (m/s)
        - temperature: 温度 (°C)
        - humidity: 湿度 (%)
        - risk_level: 风险等级
        
        返回:
        - area: 预测火灾面积 (平方公里)
        """
        # 确保数据是浮点型
        try:
            wind_speed = float(wind_speed)
            temperature = float(temperature)
            humidity = float(humidity)
        except (ValueError, TypeError) as e:
            print(f"预测面积时发生类型转换错误: {str(e)}")
            # 如果转换失败，使用默认值
            wind_speed = 10.0
            temperature = 30.0
            humidity = 60.0
            
        # 风险等级对应的基础面积
        base_area = {
            'low': 0,
            'medium': 0.5,
            'high': 2.0,
            'extreme': 5.0
        }
        
        # 如果风险级别为低，则不预测面积
        if risk_level == 'low':
            return 0
        
        # 如果risk_level不在字典中，使用medium作为默认值
        if risk_level not in base_area:
            risk_level = 'medium'
            
        try:
            # 风速因子: 风速每增加1m/s，火灾蔓延面积增加10%
            wind_factor = wind_speed * 0.1
            
            # 温度因子: 基础为1.0，温度每超过25度增加5%
            temp_factor = 1.0 + max(0, (temperature - 25) * 0.05)
            
            # 湿度因子: 湿度越高，蔓延越慢。湿度100%时因子为0，湿度0%时因子为0.8
            humidity_factor = (100 - humidity) / 125
            
            # 计算预测面积
            predicted_area = base_area[risk_level] * (1 + wind_factor) * temp_factor * (1 - humidity_factor)
            
            return round(max(0, predicted_area), 2)  # 确保面积不为负值
        except Exception as e:
            print(f"计算火灾面积时发生错误: {str(e)}")
            # 如果计算失败，返回基础面积
            return base_area.get(risk_level, 0.5)

    @staticmethod
    def analyze_monitor_data(monitor_point_id=None):
        """
        分析监测点数据，生成火灾风险评估
        
        参数:
        - monitor_point_id: 监测点ID，若不提供则分析所有监测点的最新数据
        
        返回:
        - results: 分析结果列表
        """
        results = []
        
        try:
            # 获取阈值设置
            threshold = FireThreshold.query.order_by(FireThreshold.id.desc()).first()
            
            # 查询监测数据
            if monitor_point_id:
                # 获取指定监测点的最新数据
                records = MonitorRecord.query.filter_by(monitor_point_id=monitor_point_id)\
                    .order_by(MonitorRecord.timestamp.desc()).limit(1).all()
            else:
                # 获取所有监测点的最新数据
                # 这里使用子查询获取每个监测点的最新记录ID
                latest_records_query = db.session.query(
                    MonitorRecord.monitor_point_id,
                    db.func.max(MonitorRecord.timestamp).label('max_time')
                ).group_by(MonitorRecord.monitor_point_id).subquery('latest_records')
                
                records = db.session.query(MonitorRecord).join(
                    latest_records_query,
                    db.and_(
                        MonitorRecord.monitor_point_id == latest_records_query.c.monitor_point_id,
                        MonitorRecord.timestamp == latest_records_query.c.max_time
                    )
                ).all()
            
            # 分析每条记录
            for record in records:
                try:
                    # 预测风险等级
                    risk_level = FirePredictor.predict_risk(
                        record.wind_speed, 
                        record.temperature, 
                        record.humidity,
                        threshold
                    )
                    
                    # 预测可能火灾面积
                    predicted_area = FirePredictor.predict_fire_area(
                        record.wind_speed, 
                        record.temperature, 
                        record.humidity, 
                        risk_level
                    )
                    
                    # 添加结果
                    results.append({
                        'monitor_point_id': record.monitor_point_id,
                        'monitor_point_name': record.monitor_point.name,
                        'wind_speed': record.wind_speed,
                        'temperature': record.temperature,
                        'humidity': record.humidity,
                        'risk_level': risk_level,
                        'predicted_area': predicted_area,
                        'timestamp': record.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                        'latitude': record.monitor_point.latitude,
                        'longitude': record.monitor_point.longitude
                    })
                except Exception as e:
                    print(f"分析监测记录时发生错误: {str(e)}")
                    # 跳过有问题的记录，继续处理其他记录
                    continue
        except Exception as e:
            print(f"分析监测数据时发生错误: {str(e)}")
            # 在出错时返回空结果，而不是中断程序
            
        return results 