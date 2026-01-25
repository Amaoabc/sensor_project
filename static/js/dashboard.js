// static/js/dashboard.js
/**
 * 传感器仪表板 - 主入口文件（精简版）
 */

import Utils from './utils.js';
import SensorService from './sensor-service.js';
import ChartManager from './chart-manager.js';
import UIManager from './ui-manager.js';

class SensorDashboard {
    constructor() {
        // 配置常量
        this.config = {
            autoRefreshInterval: 10000,
            chartRefreshProbability: 0.1,
            recordCountUpdateInterval: 30000,
            defaultHours: {
                co2: 24,
                tempHumi: 24
            }
        };

        // 初始化模块
        this.utils = Utils;
        this.sensorService = new SensorService({
            fetchRetries: 3,
            fetchBaseDelay: 500,
            autoRefreshInterval: this.config.autoRefreshInterval
        });

        this.chartManager = new ChartManager();
        this.uiManager = new UIManager();

        // 状态管理
        this.state = {
            autoRefreshEnabled: false,
            autoRefreshTimer: null,
            currentHours: {
                co2: this.config.defaultHours.co2,
                tempHumi: this.config.defaultHours.tempHumi
            },
            errorTracker: {
                errors: [],
                lastErrorTime: null
            }
        };

        // 初始化
        this.init();
    }

    /**
     * 初始化仪表板
     */
    async init() {
        console.log('传感器仪表板初始化开始...');

        // 检查依赖
        if (!this.checkDependencies()) {
            return;
        }

        // 绑定事件
        this.bindEvents();

        // 初始化图表
        const chartsInitialized = this.chartManager.initAllCharts();
        if (!chartsInitialized) {
            this.uiManager.showError('图表功能已禁用：Chart.js未加载。请检查static/vendor目录下的chart.min.js文件。');
        }

        // 加载初始数据
        await this.loadInitialData();

        // 启动周期性任务
        this.startPeriodicTasks();

        // 启动自动刷新
        this.startAutoRefresh();

        console.log('传感器仪表板初始化完成');
    }

    /**
     * 检查依赖
     */
    checkDependencies() {
        const dependencies = ['Chart'];
        return this.uiManager.checkAndShowDependencyWarning(dependencies);
    }

    /**
     * 绑定事件
     */
    bindEvents() {
        // 刷新按钮
        const refreshBtn = this.uiManager.getElement('refreshBtn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.fetchSensorData();
            });
        }

        // 自动刷新切换按钮
        const autoRefreshToggle = this.uiManager.getElement('autoRefreshToggle');
        if (autoRefreshToggle) {
            autoRefreshToggle.addEventListener('click', () => {
                this.toggleAutoRefresh();
            });
        }

        // 刷新所有图表按钮
        const refreshAllCharts = this.uiManager.getElement('refreshAllCharts');
        if (refreshAllCharts) {
            refreshAllCharts.addEventListener('click', () => {
                this.refreshAllCharts();
            });
        }

        // CO2时间按钮
        document.querySelectorAll('[data-chart="co2"].time-btn').forEach(button => {
            button.addEventListener('click', () => {
                this.handleTimeButtonClick(button, 'co2');
            });
        });

        // 温湿度时间按钮
        document.querySelectorAll('[data-chart="temp_humi"].time-btn').forEach(button => {
            button.addEventListener('click', () => {
                this.handleTimeButtonClick(button, 'tempHumi');
            });
        });

        // 窗口大小变化时调整图表
        window.addEventListener('resize', this.utils.debounce(() => {
            this.chartManager.resizeCharts();
        }, 250));

        // 全局错误捕获
        window.addEventListener('error', (event) => {
            this.handleGlobalError(event);
        });

        // Promise拒绝捕获
        window.addEventListener('unhandledrejection', (event) => {
            this.handlePromiseRejection(event);
        });
    }

    /**
     * 加载初始数据
     */
    async loadInitialData() {
        try {
            this.uiManager.setButtonLoading('refreshBtn', true);

            await Promise.all([
                this.fetchSensorData(),
                this.fetchChartData('co2', this.state.currentHours.co2),
                this.fetchChartData('tempHumi', this.state.currentHours.tempHumi),
                this.fetchRecordCount()
            ]);

        } catch (error) {
            console.error('加载初始数据失败:', error);
            this.uiManager.showError('加载初始数据失败，请刷新页面重试');
        } finally {
            this.uiManager.setButtonLoading('refreshBtn', false);
        }
    }

    /**
     * 处理时间按钮点击
     */
    handleTimeButtonClick(button, chartType) {
        const buttonGroup = document.querySelectorAll(`[data-chart="${chartType === 'co2' ? 'co2' : 'temp_humi'}"].time-btn`);
        buttonGroup.forEach(btn => btn.classList.remove('active'));
        button.classList.add('active');

        const hours = parseInt(button.dataset.hours) || this.config.defaultHours[chartType];
        this.state.currentHours[chartType] = hours;

        // 更新UI管理器中的按钮状态
        this.uiManager.updateTimeButtonActive(chartType === 'co2' ? 'co2' : 'temp_humi', hours);

        // 更新图表管理器的时间范围
        this.chartManager.setChartHours(chartType, hours);

        // 获取图表数据
        this.fetchChartData(chartType, hours);
    }

    /**
     * 获取传感器数据
     */
    async fetchSensorData() {
        try {
            this.uiManager.setButtonLoading('refreshBtn', true);

            const result = await this.sensorService.fetchSensorData();

            if (result.success || result.cached) {
                // 更新UI
                this.uiManager.updateSensorData(result.data);
                this.uiManager.updateSensorStatus(result.data);
                this.uiManager.hideError();
            }

            if (!result.success && !result.cached) {
                throw new Error(result.error);
            }

            return result;
        } catch (error) {
            console.error('获取传感器数据失败:', error);
            this.uiManager.showError(`传感器连接失败: ${error.message || '网络错误'}`);
            throw error;
        } finally {
            this.uiManager.setButtonLoading('refreshBtn', false);
        }
    }

    /**
     * 获取图表数据
     */
    async fetchChartData(chartType, hours) {
        try {
            const result = await this.sensorService.fetchChartData(chartType, hours);

            if (result.success || result.cached) {
                // 更新图表
                const stats = this.chartManager.updateChart(chartType, result);

                // 更新图表统计信息
                if (chartType === 'co2' && stats) {
                    this.uiManager.updateChartStats(chartType, stats);
                }
                // 更新图表统计信息
                if (chartType === 'tempHumi' && stats) {
                    this.uiManager.updateChartStats(chartType, stats);
                }

                this.uiManager.hideError();
            }

            if (!result.success && !result.cached) {
                throw new Error(result.error);
            }

            return result;
        } catch (error) {
            console.error(`获取${chartType}图表数据失败:`, error);
            this.uiManager.showError(`无法获取${chartType === 'co2' ? 'CO₂' : '温湿度'}图表数据`);
            throw error;
        }
    }

    /**
     * 获取记录数量
     */
    async fetchRecordCount() {
        try {
            const result = await this.sensorService.fetchStats();

            if (result.success && result.data.stats) {
                const count = result.data.stats.total_records || 0;
                this.uiManager.updateRecordCount(count);
            }
        } catch (error) {
            console.warn('获取记录数量失败:', error);
        }
    }

    /**
     * 刷新所有图表
     */
    refreshAllCharts() {
        this.fetchChartData('co2', this.state.currentHours.co2);
        this.fetchChartData('tempHumi', this.state.currentHours.tempHumi);
    }

    /**
     * 开始自动刷新
     */
    startAutoRefresh() {
        this.stopAutoRefresh();

        this.state.autoRefreshTimer = setInterval(() => {
            this.autoRefreshCycle();
        }, this.config.autoRefreshInterval);

        this.state.autoRefreshEnabled = true;
        this.uiManager.updateAutoRefreshButton(true);
    }

    /**
     * 停止自动刷新
     */
    stopAutoRefresh() {
        if (this.state.autoRefreshTimer) {
            clearInterval(this.state.autoRefreshTimer);
            this.state.autoRefreshTimer = null;
        }

        this.state.autoRefreshEnabled = false;
        this.uiManager.updateAutoRefreshButton(false);
    }

    /**
     * 切换自动刷新
     */
    toggleAutoRefresh() {
        if (this.state.autoRefreshEnabled) {
            this.stopAutoRefresh();
        } else {
            this.startAutoRefresh();
        }
    }

    /**
     * 自动刷新周期
     */
    async autoRefreshCycle() {
        try {
            await this.fetchSensorData();

            // 概率性刷新图表
            if (Math.random() < this.config.chartRefreshProbability) {
                this.refreshAllCharts();
            }
        } catch (error) {
            console.warn('自动刷新失败:', error);
        }
    }

    /**
     * 启动周期性任务
     */
    startPeriodicTasks() {
        // 每分钟更新本地时间显示
        setInterval(() => {
            this.uiManager.updateSensorData({ timestamp: Date.now() / 1000 });
        }, 60000);

        // 定期更新记录数量
        setInterval(() => {
            this.fetchRecordCount();
        }, this.config.recordCountUpdateInterval);
    }

    /**
     * 处理全局错误
     */
    handleGlobalError(event) {
        const errorInfo = {
            type: 'global_error',
            message: event.message,
            filename: event.filename,
            lineno: event.lineno,
            timestamp: Date.now()
        };

        this.trackError(errorInfo);
        console.error('全局错误:', errorInfo);
    }

    /**
     * 处理Promise拒绝
     */
    handlePromiseRejection(event) {
        const errorInfo = {
            type: 'unhandled_rejection',
            reason: event.reason,
            timestamp: Date.now()
        };

        this.trackError(errorInfo);
        console.error('未处理的Promise拒绝:', errorInfo);
    }

    /**
     * 跟踪错误
     */
    trackError(errorInfo) {
        this.state.errorTracker.errors.push(errorInfo);
        this.state.errorTracker.lastErrorTime = Date.now();

        // 限制错误记录数量
        if (this.state.errorTracker.errors.length > 100) {
            this.state.errorTracker.errors = this.state.errorTracker.errors.slice(-50);
        }
    }

    /**
     * 获取仪表板状态
     */
    getDashboardStatus() {
        return {
            autoRefresh: this.state.autoRefreshEnabled,
            currentHours: this.state.currentHours,
            chartStatus: this.chartManager.getChartStatus(),
            cacheStats: this.sensorService.getCacheStats(),
            errorCount: this.state.errorTracker.errors.length,
            lastErrorTime: this.state.errorTracker.lastErrorTime
        };
    }

    /**
     * 销毁仪表板
     */
    destroy() {
        this.stopAutoRefresh();
        this.chartManager.destroyCharts();
        this.sensorService.clearCache();

        console.log('仪表板已销毁');
    }
}

// 页面加载完成后初始化仪表板
document.addEventListener('DOMContentLoaded', () => {
    try {
        const dashboard = new SensorDashboard();
        window.sensorDashboard = dashboard;

        // 检查Chart.js是否加载，显示回退提示
        setTimeout(() => {
            if (typeof Chart === 'undefined') {
                dashboard.uiManager.showVendorFallback();
            }
        }, 1000);

    } catch (error) {
        console.error('仪表板初始化失败:', error);
        alert('仪表板初始化失败，请刷新页面重试');
    }
});

// 导出主类（可用于模块化导入）
export default SensorDashboard;