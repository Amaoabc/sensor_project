# app/__init__.py
"""
应用工厂模块
"""

import os
from pathlib import Path
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config.settings import Config

# 创建扩展
db = SQLAlchemy()

def create_app(config_class=Config):
    """应用工厂函数"""
    # 获取项目根目录的绝对路径
    base_dir = Path(__file__).parent.parent
    
    # 创建Flask应用，显式指定模板和静态文件目录
    app = Flask(__name__,
                template_folder=str(base_dir / 'templates'),
                static_folder=str(base_dir / 'static'))
    
    # 加载配置
    app.config.from_object(config_class)
    
    # 初始化扩展
    db.init_app(app)
    
    # 测试：检查模板目录配置
    print(f"Flask应用配置:")
    print(f"  模板目录: {app.template_folder}")
    print(f"  静态文件目录: {app.static_folder}")
    
    # 检查模板文件是否存在
    template_path = Path(app.template_folder) / 'sensor_dashboard_dual.html'
    print(f"  模板文件存在: {template_path.exists()}")
    
    # 初始化传感器管理器
    try:
        from app.sensors.manager import SensorManager
        sensor_manager = SensorManager(app)  # 传递应用实例
        app.sensor_manager = sensor_manager
    except Exception as e:
        print(f"警告: 传感器管理器初始化失败: {e}")
        app.sensor_manager = None
    
    # 注册蓝图
    try:
        from app.api.routes import api_bp
        from app.api.charts import charts_bp
        
        app.register_blueprint(api_bp, url_prefix='/api')
        app.register_blueprint(charts_bp, url_prefix='/api/chart')
    except Exception as e:
        print(f"警告: 蓝图注册失败: {e}")
    
    # 注册主路由
    @app.route('/')
    def index():
        """主页面"""
        from flask import render_template
        
        # 简化的配置，避免导入问题
        sensors = ['scd40', 'dht22']  # 简化传感器列表
        
        try:
            return render_template(
                'sensor_dashboard_dual.html',
                sensors=sensors,
                host_ip=Config.HOST,
                port=Config.PORT,
                app_version="4.0",
                timezone_offset=Config.TIMEZONE_OFFSET
            )
        except Exception as e:
            return f"模板渲染错误: {str(e)}", 500
    
    @app.route('/favicon.ico')
    def favicon():
        """favicon重定向"""
        from flask import redirect, url_for
        try:
            return redirect(url_for('static', filename='favicon.svg'))
        except Exception:
            return ('', 204)
    
    # 在应用上下文中初始化数据库
    with app.app_context():
        # 导入模型并创建表
        try:
            from app.models import SensorData
            db.create_all()
            print("✅ 数据库表已创建")
        except Exception as e:
            print(f"❌ 数据库表创建失败: {e}")
        
        # 启动传感器管理器
        if app.sensor_manager:
            try:
                app.sensor_manager.start_collection(app)
                print("✅ 传感器管理器已启动")
            except Exception as e:
                print(f"❌ 传感器管理器启动失败: {e}")
    
    return app