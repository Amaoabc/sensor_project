# app/utils/data_utils.py
"""
数据处理工具模块
"""

import random
import math
from datetime import datetime, timedelta
from config.logging_config import get_logger

logger = get_logger(__name__)

def generate_sample_data(data_type, hours):
    """生成示例数据"""
    if data_type == 'co2':
        return generate_co2_sample_data(hours)
    elif data_type == 'temp_humi':
        return generate_temp_humi_sample_data(hours)
    else:
        raise ValueError(f"未知的数据类型: {data_type}")

def generate_co2_sample_data(hours):
    """生成CO2示例数据"""
    from app.utils.time_utils import get_local_now
    
    # 生成时间标签
    labels = []
    data = []
    
    # 根据小时数确定数据点数量
    if hours <= 1:
        points = 30  # 1小时，每2分钟一个点
    elif hours <= 6:
        points = 36   # 6小时，每10分钟一个点
    elif hours <= 24:
        points = 48   # 24小时，每30分钟一个点
    else:
        points = 56   # 7天，每3小时一个点
    
    # 获取当前时间
    now_local = get_local_now()
    start_time = now_local - timedelta(hours=hours)
    
    base_value = 650
    for i in range(points):
        # 计算时间点
        point_time = start_time + timedelta(hours=hours * i / points)
        
        # 生成时间标签
        if hours <= 24:
            labels.append(point_time.strftime('%H:%M'))
        else:
            labels.append(point_time.strftime('%m-%d %H:%M'))
        
        # 生成CO2数据
        if hours <= 1:
            variation = 50 * math.sin(i / 5) + random.uniform(-20, 20)
        elif hours <= 6:
            time_of_day = (i % points) / points
            variation = 100 * math.sin(time_of_day * 2 * math.pi) + random.uniform(-30, 30)
        else:
            variation = 150 * math.sin(i / 15) + random.uniform(-50, 50)
        
        data.append(max(400, min(1500, int(base_value + variation))))
    
    return {
        'success': True,
        'count': points,
        'labels': labels,
        'datasets': [{
            'label': 'CO₂浓度 (示例数据)',
            'data': data,
            'borderColor': 'rgb(76, 201, 240)',
            'backgroundColor': 'rgba(76, 201, 240, 0.1)',
            'borderWidth': 2,
            'tension': 0.4
        }],
        'units': 'ppm',
        'source': 'SCD40 (示例数据)',
        'range': {
            'min': min(data),
            'max': max(data),
            'avg': sum(data)/len(data)
        }
    }

def generate_temp_humi_sample_data(hours):
    """生成温湿度示例数据"""
    from app.utils.time_utils import get_local_now
    
    # 生成时间标签
    labels = []
    temp_data = []
    humi_data = []
    
    # 根据小时数确定数据点数量
    if hours <= 1:
        points = 30
    elif hours <= 6:
        points = 36
    elif hours <= 24:
        points = 48
    else:
        points = 56
    
    # 获取当前时间
    now_local = get_local_now()
    start_time = now_local - timedelta(hours=hours)
    
    temp_base = 23.0
    humi_base = 58.0
    
    for i in range(points):
        # 计算时间点
        point_time = start_time + timedelta(hours=hours * i / points)
        
        # 生成时间标签
        if hours <= 24:
            labels.append(point_time.strftime('%H:%M'))
        else:
            labels.append(point_time.strftime('%m-%d %H:%M'))
        
        # 生成温度数据
        if hours <= 1:
            temp_variation = 1.5 * math.sin(i / 3) + random.uniform(-0.5, 0.5)
        elif hours <= 6:
            time_of_day = (i % points) / points
            temp_variation = 3 * math.sin(time_of_day * 2 * math.pi) + random.uniform(-1, 1)
        else:
            temp_variation = 4 * math.sin(i / 12) + random.uniform(-1.5, 1.5)
        
        temp_data.append(round(max(18, min(30, temp_base + temp_variation)), 1))
        
        # 生成湿度数据
        if hours <= 1:
            humi_variation = -5 * math.sin(i / 3) + random.uniform(-3, 3)
        elif hours <= 6:
            time_of_day = (i % points) / points
            humi_variation = -15 * math.sin(time_of_day * 2 * math.pi) + random.uniform(-5, 5)
        else:
            humi_variation = -20 * math.sin(i / 12) + random.uniform(-8, 8)
        
        humi_data.append(max(30, min(80, round(humi_base + humi_variation, 1))))
    
    return {
        'success': True,
        'count': points,
        'labels': labels,
        'datasets': [
            {
                'label': '温度 (示例数据)',
                'data': temp_data,
                'borderColor': 'rgb(247, 37, 133)',
                'backgroundColor': 'rgba(247, 37, 133, 0.1)',
                'borderWidth': 2,
                'tension': 0.4,
                'yAxisID': 'y'
            },
            {
                'label': '湿度 (示例数据)',
                'data': humi_data,
                'borderColor': 'rgb(74, 214, 109)',
                'backgroundColor': 'rgba(74, 214, 109, 0.1)',
                'borderWidth': 2,
                'tension': 0.4,
                'yAxisID': 'y1'
            }
        ],
        'units': {
            'temperature': '°C',
            'humidity': '%'
        },
        'sources': {
            'temperature': 'DHT22 (示例数据)',
            'humidity': 'DHT22 (示例数据)'
        }
    }