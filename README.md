# README.md

# 树莓派环境监测系统

基于树莓派的双传感器（SCD40 CO₂传感器 + DHT22温湿度传感器）环境监测系统，提供实时数据采集、Web可视化界面和API接口。

## 功能特性

### 🎯 核心功能
- **实时监测**：同时采集CO₂浓度、温度、湿度数据
- **双传感器融合**：SCD40（CO₂） + DHT22（温湿度）协同工作
- **数据过滤**：智能数据过滤算法，排除异常值
- **历史记录**：SQLite数据库存储历史数据
- **RESTful API**：完整的API接口，支持数据查询
- **Web仪表板**：响应式Web界面，实时图表展示

### 📊 监测指标
| 指标 | 传感器 | 测量范围 | 精度 |
|------|--------|----------|------|
| CO₂浓度 | SCD40 | 0-5000 ppm | ±(40ppm + 5%) |
| 温度 | DHT22 | -40~80°C | ±0.5°C |
| 相对湿度 | DHT22 | 0-100% RH | ±2% RH |

### 🌐 Web界面功能
- 实时数据显示与刷新
- CO₂浓度历史趋势图
- 温湿度历史趋势图
- 传感器状态监控
- 自动/手动刷新模式
- 时区自适应显示

## 项目结构

```
sensor_project/
├── app/                    # Flask应用核心模块
│   ├── __init__.py        # 应用工厂模块
│   ├── models.py          # SQLAlchemy数据模型
│   ├── sensors/           # 传感器驱动模块
│   │   ├── manager.py     # 传感器管理器
│   │   ├── data_filter.py # 传感器数据过滤器
│   │   ├── scd40.py       # SCD40传感器驱动
│   │   └── dht22.py       # DHT22传感器驱动
│   ├── utils/             # 工具模块
│   │   ├── __init__.py    # 工具模块包
│   │   ├── time_utils.py  # 时间处理工具
│   │   └── data_utils.py  # 数据处理工具
│   └── api/               # API接口模块
│       ├── __init__.py    # API模块包
│       ├── routes.py      # 主API路由
│       └── charts.py      # 图表数据API
├── config/                # 配置文件目录
│   ├── settings.py        # 主配置文件
│   ├── sensors.py         # 传感器配置
│   └── logging_config.py  # 日志配置
├── static/               # 静态资源
│   ├── css/              # 样式文件
│   │   └── dashboard.css # 传感器仪表板样式
│   ├── js/               # JavaScript文件
│   ├── vendor/           # 第三方库
│   └── favicon.svg       # 网站图标
├── templates/            # HTML模板
│   └── sensor_dashboard_dual.html
├── venv/                 # Python虚拟环境
├── sensor_api_dual_v4.py # 主启动文件
├── requirements.txt      # Python依赖包
├── README.md            # 项目说明（本文档）
└── sensor_data_dual.db  # SQLite数据库（运行时生成）
```

## 硬件要求

### 必需硬件
- **树莓派**（3B/4B/Zero 2W等）
- **SCD40传感器**（I2C接口，测量CO₂浓度）
- **DHT22传感器**（单总线接口，测量温湿度）
- **杜邦线**若干

### 连接方式
```
树莓派 GPIO 引脚布局：
    SCD40 (I2C接口):
        VCC  -> Pin 1 (3.3V)
        GND  -> Pin 6 (GND)
        SDA  -> Pin 3 (GPIO2/SDA)
        SCL  -> Pin 5 (GPIO3/SCL)
    
    DHT22 (单总线):
        VCC  -> Pin 1 (3.3V)
        GND  -> Pin 9 (GND)
        DATA -> Pin 7 (GPIO4)
```

## 软件环境

### 系统要求
- **操作系统**: Raspberry Pi OS (基于Debian)
- **Python版本**: Python 3.7+
- **包管理**: pip3

### Python依赖包
```bash
# 查看完整依赖列表
cat requirements.txt
```

主要依赖包：
- Flask ~= 2.3.0
- Flask-SQLAlchemy ~= 3.0.0
- Adafruit-Blinka ~= 8.0.0
- Adafruit-SCD4x ~= 2.2.2
- Adafruit-DHT ~= 1.4.0

## 快速开始

### 1. 环境准备
```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装Python3和pip
sudo apt install python3 python3-pip python3-venv -y

# 启用I2C接口
sudo raspi-config
# 选择 Interface Options -> I2C -> Yes
```

### 2. 克隆/下载项目
```bash
# 进入项目目录
cd /home/admin/sensor_project
```

### 3. 创建虚拟环境
```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate
```

### 4. 安装依赖
```bash
# 安装Python包
pip install -r requirements.txt

# 或者逐个安装主要包
pip install Flask Flask-SQLAlchemy Adafruit-Blinka Adafruit-SCD4x Adafruit-DHT
```

### 5. 配置传感器
确保SCD40和DHT22传感器已正确连接到树莓派，然后测试传感器：

```bash
# 测试I2C设备是否被识别
sudo i2cdetect -y 1

# 应能看到地址0x62（SCD40）
```

### 6. 启动服务
```bash
# 直接运行主程序
python sensor_api_dual_v4.py&


```

### 7. 访问Web界面
打开浏览器，访问：`http://树莓派IP地址:5000`

## API接口文档

### 实时数据接口
```
GET /api/environment
返回当前所有传感器数据
```

### 历史数据接口
```
GET /api/history
参数：
  - limit: 记录条数（默认100，最大1000）
  - start_time: 起始时间（ISO格式）
  - end_time: 结束时间（ISO格式）
```

### 健康检查接口
```
GET /api/health
返回系统组件状态
```

### 统计信息接口
```
GET /api/stats
返回数据统计信息
```

### 图表数据接口
```
GET /api/chart/co2
参数：
  - hours: 时间范围（1, 6, 24, 168小时）
```

## 配置文件说明

### 主要配置文件

#### `config/settings.py` - 主配置
- 服务器设置（主机、端口）
- 数据库配置
- API参数
- 时区设置

#### `config/sensors.py` - 传感器配置
- 传感器参数（引脚、地址）
- 数据过滤设置
- 有效范围验证

#### `config/logging_config.py` - 日志配置
- 日志级别设置
- 日志文件输出
- 日志格式

## 自定义配置

### 修改采集间隔
编辑 `config/sensors.py`：
```python
DATA_COLLECTION = {
    'interval': 10,  # 改为5秒采集一次
    # ...
}
```

### 修改数据过滤参数
```python
DHT22_CONFIG = {
    'data_filter': {
        'enabled': True,
        'window_size': 10,  # 增大滑动窗口
        'temperature': {
            'max_change': 3.0,  # 减小最大温度变化
        }
    }
}
```

### 修改时区
```bash
# 启动时设置环境变量
TIMEZONE_OFFSET=8 python sensor_api_dual_v4.py

# 或直接修改 config/settings.py
TIMEZONE_OFFSET = 8  # 东八区
```

## 系统管理

### 查看日志
```bash
# 查看应用日志
tail -f sensor_api_dual.log

# 查看错误日志
tail -f sensor_api_dual_error.log

# 查看系统日志
journalctl -u sensor_dual.service
```

### 数据库管理
```bash
# 使用sqlite3查看数据库
sqlite3 sensor_data_dual.db

# 常用SQLite命令
.tables                    # 查看所有表
SELECT COUNT(*) FROM sensor_data;  # 查看记录数
.schema sensor_data        # 查看表结构
```

### 服务管理（使用systemd）

创建systemd服务文件 `/etc/systemd/system/sensor_dual.service`：
```ini
[Unit]
Description=树莓派双传感器环境监测服务 (v4.0)
After=network.target

[Service]
Type=simple
User=admin
WorkingDirectory=/home/admin/sensor_project
Environment=PATH=/home/admin/sensor_project/venv/bin
Environment=PYTHONPATH=/home/admin/sensor_project
ExecStart=/home/admin/sensor_project/venv/bin/python /home/admin/sensor_project/sensor_api_dual_v4.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target

```

启用并启动服务：
```bash
sudo systemctl daemon-reload
sudo systemctl enable sensor_dual.service
sudo systemctl start sensor_dual.service
sudo systemctl status sensor_dual.service
```

## 故障排除

### 常见问题

#### 1. SCD40传感器无法识别
```bash
# 检查I2C设备
sudo i2cdetect -y 1

# 检查I2C是否启用
lsmod | grep i2c

# 检查权限
groups $USER | grep i2c
```

#### 2. DHT22读取失败
- 检查接线是否正确
- 检查GPIO引脚号配置
- 尝试降低读取频率

#### 3. Web界面无法访问
- 检查树莓派防火墙
- 确认服务正在运行
- 检查网络连接

#### 4. 数据库错误
```bash
# 备份并重建数据库
cp sensor_data_dual.db sensor_data_dual.db.backup
rm sensor_data_dual.db
python -c "from app import db; db.create_all()"
```

### 调试模式
```bash
# 启用调试模式
export FLASK_DEBUG=True
python sensor_api_dual_v4.py
```

## 项目开发

### 代码结构说明
- `app/sensors/` - 传感器驱动层，可扩展其他传感器
- `app/api/` - API接口层，可添加新接口
- `app/utils/` - 工具函数，可复用
- `config/` - 配置文件，支持环境变量覆盖

### 扩展新传感器
1. 在 `app/sensors/` 目录下创建新传感器类
2. 在 `config/sensors.py` 中添加配置
3. 在 `app/sensors/manager.py` 中注册传感器
4. 更新数据模型和API接口

### 添加新图表
1. 在 `app/api/charts.py` 中添加新的图表数据接口
2. 在前端 `static/js/dashboard.js` 中添加对应的图表初始化
3. 在模板中增加图表容器

## 性能优化

### 数据采集优化
- 调整采集间隔（默认10秒）
- 启用数据过滤，减少异常值
- 批量写入数据库，减少IO操作

### 数据库优化
- 定期清理旧数据
- 建立时间索引
- 考虑分区表（按时间分区）

### Web界面优化
- 启用客户端缓存
- 压缩静态资源
- 使用CDN加速第三方库

## 安全注意事项

### 网络安全
- 不建议在公网直接暴露服务
- 使用防火墙限制访问IP
- 考虑添加认证机制

### 数据安全
- 定期备份数据库
- 加密敏感配置信息
- 实施访问日志记录

### 系统安全
- 使用非root用户运行服务
- 定期更新系统和软件包
- 监控系统资源使用

## 许可证

本项目采用 MIT 许可证。详见 LICENSE 文件（如果需要）。

## 贡献指南

欢迎提交Issue和Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启一个 Pull Request

## 联系方式

如有问题或建议，请通过以下方式联系：

- 提交 Issue
- 项目维护者：admin@RaspberryPi

---

**最后更新**: 2026年1月25日  
**版本**: v4.0  
**状态**: 开发中
```


123test