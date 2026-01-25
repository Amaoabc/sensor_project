#!/usr/bin/env python3
"""
树莓派双传感器API服务 - 精简版本 v4.0
基于模块化架构
"""

import sys
from pathlib import Path

# 添加app目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

# 导入配置
from config.settings import Config
from config.logging_config import setup_logging
from app.utils.time_utils import get_local_now

# 初始化日志
logger = setup_logging(
    app_name='sensor_api_dual',
    log_level='info',
    log_to_file=True
)

# 导入应用工厂
from app import create_app

def test_sensors(app):
    """测试所有传感器功能"""
    print("\n" + "=" * 60)
    print("测试传感器...")
    print("=" * 60)
    
    results = app.sensor_manager.test_sensors()
    
    for sensor_name, result in results.items():
        if result['status'] == 'passed':
            if sensor_name == 'scd40':
                print(f"✅ {sensor_name.upper()}测试成功: CO2={result['co2']}ppm")
            else:
                print(f"✅ {sensor_name.upper()}测试成功: 温度={result['temperature']}°C, 湿度={result['humidity']}%")
        elif result['status'] == 'failed':
            print(f"⚠️ {sensor_name.upper()}读数异常: {result.get('error', '未知错误')}")
        elif result['status'] == 'error':
            print(f"❌ {sensor_name.upper()}测试错误: {result.get('error', '未知错误')}")
        else:
            print(f"❌ {sensor_name.upper()}传感器离线")
    
    print("=" * 60)
    
    passed_tests = sum(1 for result in results.values() if result['status'] == 'passed')
    if passed_tests > 0:
        print(f"✅ {passed_tests}/{len(results)} 个传感器测试通过")
    else:
        print("⚠️ 警告: 没有传感器测试通过，服务可能无法正常工作")

def main():
    """主函数"""
    # 创建Flask应用
    app = create_app()
    
    print("=" * 60)
    print("树莓派双传感器环境监测系统 v4.0")
    print("=" * 60)
    print(f"启动时间 (UTC): {get_local_now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("传感器状态:")
    sensor_status = app.sensor_manager.get_sensor_status()
    print(f"  • SCD40: {'✅ 已连接' if sensor_status.get('scd40') == 'online' else '❌ 未连接'} (仅CO2)")
    print(f"  • DHT22: {'✅ 已连接' if sensor_status.get('dht22') == 'online' else '❌ 未连接'} (温湿度)")
    print(f"时区设置: UTC+{Config.TIMEZONE_OFFSET}")
    print(f"服务器地址: http://{Config.HOST}:{Config.PORT}")
    print("=" * 60)
    
    # 测试传感器
    test_sensors(app)
    
    print("提示: 数据采集线程已启动，将持续记录传感器数据")
    print("提示: 按 Ctrl+C 停止服务")
    print("=" * 60)
    
    try:
        # 运行应用
        app.run(
            host=Config.HOST,
            port=Config.PORT,
            debug=Config.DEBUG,
            threaded=True,
            use_reloader=False
        )
    except KeyboardInterrupt:
        logger.info("服务被用户中断")
        print("\n服务已停止")
    except Exception as e:
        logger.error(f"服务启动失败: {e}")
        print(f"服务启动失败: {e}")

if __name__ == '__main__':
    main()