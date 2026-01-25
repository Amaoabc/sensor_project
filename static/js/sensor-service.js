// static/js/sensor-service.js
/**
 * 传感器API服务模块 - 处理所有API请求
 */

import Utils from './utils.js';

class SensorService {
    constructor(config = {}) {
        this.config = {
            fetchRetries: config.fetchRetries || 3,
            fetchBaseDelay: config.fetchBaseDelay || 500,
            autoRefreshInterval: config.autoRefreshInterval || 10000,
            ...config
        };
        
        // 请求缓存
        this.cache = new Map();
        this.cacheDuration = 2000; // 2秒缓存
    }

    /**
     * 带重试的fetch请求
     */
    async fetchWithRetry(url, options = {}) {
        let lastError;

        for (let attempt = 0; attempt < this.config.fetchRetries; attempt++) {
            try {
                const response = await fetch(url, {
                    ...options,
                    headers: {
                        'Accept': 'application/json',
                        ...options.headers
                    }
                });

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }

                return await response.json();
            } catch (error) {
                lastError = error;

                if (attempt < this.config.fetchRetries - 1) {
                    const delay = this.config.fetchBaseDelay * Math.pow(2, attempt);
                    await Utils.sleep(delay);
                }
            }
        }

        throw lastError;
    }

    /**
     * 获取环境数据
     */
    async fetchSensorData() {
        try {
            const data = await this.fetchWithRetry('/api/environment');
            
            // 缓存数据
            this.cache.set('environment', {
                data,
                timestamp: Date.now()
            });
            
            return {
                success: true,
                data,
                timestamp: Date.now()
            };
        } catch (error) {
            console.error('获取传感器数据失败:', error);
            
            // 尝试使用缓存
            const cached = this.cache.get('environment');
            if (cached && Date.now() - cached.timestamp < this.cacheDuration * 5) {
                console.warn('使用缓存的环境数据');
                return {
                    success: false,
                    data: cached.data,
                    timestamp: cached.timestamp,
                    error: error.message,
                    cached: true
                };
            }
            
            return {
                success: false,
                error: error.message,
                data: null
            };
        }
    }

    /**
     * 获取图表数据
     */
    async fetchChartData(chartType, hours = 24) {
        const endpoint = chartType === 'co2' 
            ? '/api/chart/co2' 
            : '/api/chart/temperature_humidity';
        
        const url = `${endpoint}?hours=${hours}`;
        const cacheKey = `${chartType}_${hours}`;
        
        try {
            const data = await this.fetchWithRetry(url);
            
            // 缓存数据
            this.cache.set(cacheKey, {
                data,
                timestamp: Date.now()
            });
            
            return {
                success: true,
                data,
                chartType,
                hours,
                timestamp: Date.now()
            };
        } catch (error) {
            console.error(`获取${chartType}图表数据失败:`, error);
            
            // 尝试使用缓存
            const cached = this.cache.get(cacheKey);
            if (cached) {
                console.warn(`使用缓存的${chartType}图表数据`);
                return {
                    success: false,
                    data: cached.data,
                    chartType,
                    hours,
                    timestamp: cached.timestamp,
                    error: error.message,
                    cached: true
                };
            }
            
            return {
                success: false,
                error: error.message,
                data: null
            };
        }
    }

    /**
     * 获取统计信息
     */
    async fetchStats() {
        try {
            const response = await fetch('/api/stats');
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const data = await response.json();
            return {
                success: true,
                data
            };
        } catch (error) {
            console.error('获取统计信息失败:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * 获取健康状态
     */
    async fetchHealth() {
        try {
            const data = await this.fetchWithRetry('/api/health');
            return {
                success: true,
                data
            };
        } catch (error) {
            console.error('获取健康状态失败:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * 清除缓存
     */
    clearCache() {
        this.cache.clear();
        console.log('API缓存已清除');
    }

    /**
     * 获取缓存统计
     */
    getCacheStats() {
        return {
            size: this.cache.size,
            keys: Array.from(this.cache.keys())
        };
    }
}

// 导出服务类
export default SensorService;