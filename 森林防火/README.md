# 森林防火预测监测系统

## 项目简介
本系统是一个基于Web的森林防火预测监测系统，用于实时监控森林环境参数，预测潜在火灾风险并进行数据统计分析。

## 主要功能
用户管理：管理所有系统用户
管理员权限管理：指定用户设置为管理员
监测信息管理：监控风速、温度、湿度等环境参数
火灾预测：基于监测数据进行火灾风险预警和面积预测
火灾信息管理：设置预警阈值及参数配置
火灾数据统计：统计区域内火灾数量、位置和参数

## 技术栈
后端：Python + Flask
前端：HTML + CSS + JavaScript + Bootstrap
数据库：MySQL
数据分析：NumPy, Pandas, Scikit-learn

## 安装和启动
1. 创建并激活虚拟环境
```
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

2. 安装依赖
```
pip install -r requirements.txt
```

3. 启动应用
```
python app.py
```

## 访问系统
浏览器访问 http://localhost:5000 

我们使用的计算方法：
火灾风险评估：基于风速、温度和湿度计算风险得分，然后根据得分判断风险等级（低、中、高、极高）。
火灾面积预测：根据公式"面积 = 基础面积 × (1 + 风速因子) × 温度因子 × (1 - 湿度因子)"计算。