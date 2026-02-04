/**
 * UI管理模块 - 处理所有UI状态更新
 */

import Utils from './utils.js';

class UIManager {
    constructor() {
        this.elements = {};
        this.cacheElements();
    }

    /**
     * 缓存DOM元素
     */
    cacheElements() {
        const selectors = {
            co2Value: '#co2Value',
            tempValue: '#tempValue',
            humiValue: '#humiValue',
            scd40Status: '#scd40Status',
            dht22Status: '#dht22Status',
            lastUpdatedTime: '#lastUpdatedTime',
            localTime: '#localTime',
            errorMessage: '#errorMessage',
            errorText: '#errorText',
            refreshBtn: '#refreshBtn',
            autoRefreshToggle: '#autoRefreshToggle',
            refreshAllCharts: '#refreshAllCharts',
            recordCount: '#recordCount',
            co2Min: '#co2Min',
            co2Max: '#co2Max',
            co2Source: '#co2Source',
            tempRange: '#tempRange',
            humiRange: '#humiRange',
            vendorFallback: '#vendorFallback',
            sgp41Status: '#sgp41Status',
            vocValue: '#vocValue',
            noxValue: '#noxValue',
            vocRange: '#vocRange',
            noxRange: '#noxRange',
            vocNoxSource: '#vocNoxSource'
        };

        console.log('开始缓存DOM元素...');

        Object.keys(selectors).forEach(key => {
            const element = document.querySelector(selectors[key]);
            this.elements[key] = element;

            if (element) {
                console.log(`✅ 已缓存: ${key} -> ${selectors[key]}`);
            } else {
                console.warn(`❌ 未找到: ${key} -> ${selectors[key]}`);
            }
        });

        console.log('DOM元素缓存完成');
    }

    /**
     * 更新传感器数据显示
     */
    updateSensorData(sensorData) {
        if (!sensorData || !sensorData.sensors) return;

        // 安全地解构传感器数据，提供默认值
        const sensors = sensorData.sensors || {};
        const scd40 = sensors.scd40 || {};
        const dht22 = sensors.dht22 || {};
        const sgp41 = sensors.sgp41 || {};  // 添加默认值

        // 更新CO2值
        if (this.elements.co2Value) {
            const co2 = scd40.co2;
            this.elements.co2Value.textContent = co2 !== null && co2 !== undefined ? co2 : '--';
            this.elements.co2Value.classList.toggle('loading', co2 === null);
        }

        // 更新温度值
        if (this.elements.tempValue) {
            const temp = dht22.temperature;
            this.elements.tempValue.textContent = temp !== null && temp !== undefined ? temp : '--';
            this.elements.tempValue.classList.toggle('loading', temp === null);
        }

        // 更新湿度值
        if (this.elements.humiValue) {
            const humi = dht22.humidity;
            this.elements.humiValue.textContent = humi !== null && humi !== undefined ? humi : '--';
            this.elements.humiValue.classList.toggle('loading', humi === null);
        }
        // 更新VOC值
        if (this.elements.vocValue) {
            const voc = sgp41.voc_index;
            this.elements.vocValue.textContent = voc !== null && voc !== undefined ? Math.round(voc) : '--';
            this.elements.vocValue.classList.toggle('loading', voc === null);
        }

        // 更新NOx值
        if (this.elements.noxValue) {
            const nox = sgp41.nox_index;
            this.elements.noxValue.textContent = nox !== null && nox !== undefined ? Math.round(nox) : '--';
            this.elements.noxValue.classList.toggle('loading', nox === null);
        }

        // 更新最后更新时间
        if (this.elements.lastUpdatedTime && sensorData.timestamp) {
            try {
                const tzOffset = window.SERVER_TZ_OFFSET || 8;
                const date = new Date(sensorData.timestamp * 1000);
                const utc = date.getTime() + (date.getTimezoneOffset() * 60000);
                const localTime = new Date(utc + (tzOffset * 3600000));

                const timeString = localTime.toLocaleTimeString('zh-CN', {
                    hour12: false,
                    hour: '2-digit',
                    minute: '2-digit',
                    second: '2-digit'
                });

                this.elements.lastUpdatedTime.textContent = timeString;
            } catch (error) {
                console.warn('时间格式化失败:', error);
                this.elements.lastUpdatedTime.textContent = '--';
            }
        }

        // 更新本地时间显示
        if (this.elements.localTime) {
            this.elements.localTime.textContent = `时间: ${Utils.formatTime(new Date())}`;
        }
    }

    /**
     * 更新传感器状态
     */
    updateSensorStatus(sensorData) {
        if (!sensorData || !sensorData.sensors) return;

        const sensors = sensorData.sensors || {};
        const scd40 = sensors.scd40 || {};
        const dht22 = sensors.dht22 || {};
        const sgp41 = sensors.sgp41 || {};  // 添加默认值

        // 更新SCD40状态
        if (this.elements.scd40Status) {
            const status = scd40.status || 'offline';
            this.updateStatusElement(this.elements.scd40Status, 'SCD40', status);
        }

        // 更新DHT22状态
        if (this.elements.dht22Status) {
            const status = dht22.status || 'offline';
            this.updateStatusElement(this.elements.dht22Status, 'DHT22', status);
        }
        // 更新SGP41状态
        if (this.elements.sgp41Status) {
            const status = sgp41.status || 'offline';
            this.updateStatusElement(this.elements.sgp41Status, 'SGP41', status);
        }
    }

    /**
     * 更新状态元素
     */
    updateStatusElement(element, sensorName, status) {
        const statusConfig = {
            online: { className: 'status-item status-online', icon: 'fa-check-circle', text: '在线' },
            degraded: { className: 'status-item status-degraded', icon: 'fa-exclamation-circle', text: '降级' },
            offline: { className: 'status-item status-offline', icon: 'fa-times-circle', text: '离线' }
        };

        const config = statusConfig[status] || statusConfig.offline;
        element.className = config.className;
        element.innerHTML = `<i class="fas ${config.icon}"></i> ${sensorName}: ${config.text}`;
    }

    /**
     * 更新图表统计信息
     */
    updateChartStats(chartType, stats) {
        if (!stats) return;

        switch (chartType) {
            case 'co2':
                if (this.elements.co2Min && this.elements.co2Max) {
                    const { min, max } = stats;
                    this.elements.co2Min.textContent = min !== undefined ? `${min.toFixed(0)} ppm` : '--';
                    this.elements.co2Max.textContent = max !== undefined ? `${max.toFixed(0)} ppm` : '--';
                }
                break;

            case 'tempHumi':
                // 温湿度图表的stats应该包含temperature和humidity两个属性
                const { temperature, humidity } = stats;
                
                // 更新温度范围
                if (this.elements.tempRange && temperature) {
                    const { min: tempMin, max: tempMax } = temperature;
                    if (tempMin !== undefined && tempMax !== undefined) {
                        this.elements.tempRange.textContent = `${tempMin.toFixed(1)}°C ~ ${tempMax.toFixed(1)}°C`;
                    } else if (tempMin !== undefined) {
                        this.elements.tempRange.textContent = `${tempMin.toFixed(1)}°C`;
                    } else if (tempMax !== undefined) {
                        this.elements.tempRange.textContent = `${tempMax.toFixed(1)}°C`;
                    } else {
                        this.elements.tempRange.textContent = '--';
                    }
                }
                
                // 更新湿度范围
                if (this.elements.humiRange && humidity) {
                    const { min: humiMin, max: humiMax } = humidity;
                    if (humiMin !== undefined && humiMax !== undefined) {
                        this.elements.humiRange.textContent = `${humiMin.toFixed(1)}% ~ ${humiMax.toFixed(1)}%`;
                    } else if (humiMin !== undefined) {
                        this.elements.humiRange.textContent = `${humiMin.toFixed(1)}%`;
                    } else if (humiMax !== undefined) {
                        this.elements.humiRange.textContent = `${humiMax.toFixed(1)}%`;
                    } else {
                        this.elements.humiRange.textContent = '--';
                    }
                }
                break;
            case 'vocNox':                    
                    const { voc, nox } = stats;                    
                    // 更新VOC范围
                    if (this.elements.vocRange && voc) {
                        const { min: vocMin, max: vocMax } = voc;
                        if (vocMin !== undefined && vocMax !== undefined) {
                            this.elements.vocRange.textContent = `${vocMin.toFixed(0)} ~ ${vocMax.toFixed(0)} index`;
                        } else if (vocMin !== undefined) {
                            this.elements.vocRange.textContent = `${vocMin.toFixed(0)} index`;
                        } else if (vocMax !== undefined) {
                            this.elements.vocRange.textContent = `${vocMax.toFixed(0)} index`;
                        } else {
                            this.elements.vocRange.textContent = '--';
                        }
                    }
                    // 更新NOx范围
                    if (this.elements.noxRange && nox) {
                        const { min: noxMin, max: noxMax } = nox;
                        if (noxMin !== undefined && noxMax !== undefined) {
                            this.elements.noxRange.textContent = `${noxMin.toFixed(0)} ~ ${noxMax.toFixed(0)} index`;
                        } else if (noxMin !== undefined) {
                            this.elements.noxRange.textContent = `${noxMin.toFixed(0)} index`;
                        } else if (noxMax !== undefined) {
                            this.elements.noxRange.textContent = `${noxMax.toFixed(0)} index`;
                        } else {
                            this.elements.noxRange.textContent = '--';
                        }
                    }
        }
    }

    /**
     * 更新记录数量
     */
    updateRecordCount(count) {
        if (this.elements.recordCount) {
            this.elements.recordCount.textContent = count.toLocaleString();
        }
    }

    /**
     * 显示错误消息
     */
    showError(message, duration = 5000) {
        if (!this.elements.errorMessage || !this.elements.errorText) return;

        this.elements.errorText.textContent = message;
        this.elements.errorMessage.style.display = 'block';

        // 自动隐藏
        if (duration > 0) {
            setTimeout(() => {
                this.hideError();
            }, duration);
        }
    }

    /**
     * 隐藏错误消息
     */
    hideError() {
        if (this.elements.errorMessage) {
            this.elements.errorMessage.style.display = 'none';
        }
    }

    /**
     * 更新自动刷新按钮状态
     */
    updateAutoRefreshButton(enabled) {
        if (!this.elements.autoRefreshToggle) return;

        if (enabled) {
            this.elements.autoRefreshToggle.innerHTML = '<i class="fas fa-pause"></i> 停止自动刷新';
            this.elements.autoRefreshToggle.classList.add('active');
        } else {
            this.elements.autoRefreshToggle.innerHTML = '<i class="fas fa-play"></i> 自动刷新 (10秒)';
            this.elements.autoRefreshToggle.classList.remove('active');
        }
    }

    /**
     * 更新按钮加载状态
     */
    setButtonLoading(buttonId, isLoading) {
        let button;

        // 如果传入的是字符串
        if (typeof buttonId === 'string') {
            // 如果是选择器（以 # 或 . 开头）
            if (buttonId.startsWith('#') || buttonId.startsWith('.')) {
                button = document.querySelector(buttonId);
            }
            // 如果是元素ID（没有前缀）
            else {
                // 首先尝试从缓存中获取
                button = this.elements[buttonId];

                // 如果缓存中没有，尝试作为ID选择器查找
                if (!button) {
                    button = document.getElementById(buttonId);
                }

                // 如果还没有找到，尝试作为其他选择器
                if (!button) {
                    button = document.querySelector(`#${buttonId}`);
                }
            }
        }
        // 如果传入的是DOM元素
        else if (buttonId && buttonId.nodeType) {
            button = buttonId;
        }

        if (button) {
            button.classList.toggle('loading', isLoading);
            button.disabled = isLoading;
            console.log(`按钮 ${buttonId} 加载状态设置为: ${isLoading}`);
        } else {
            console.warn(`未找到按钮元素: ${buttonId}`);

            // 调试信息：显示所有缓存元素
            console.log('当前缓存元素:', this.elements);
        }
    }

    /**
     * 更新时间按钮激活状态
     */
    updateTimeButtonActive(chartType, hours) {
        const buttons = document.querySelectorAll(`[data-chart="${chartType}"].time-btn`);
        buttons.forEach(button => {
            const buttonHours = parseInt(button.dataset.hours) || 0;
            button.classList.toggle('active', buttonHours === hours);
        });
    }

    /**
     * 显示vendor回退提示
     */
    showVendorFallback() {
        if (this.elements.vendorFallback) {
            this.elements.vendorFallback.style.display = 'block';
        }
    }

    /**
     * 隐藏vendor回退提示
     */
    hideVendorFallback() {
        if (this.elements.vendorFallback) {
            this.elements.vendorFallback.style.display = 'none';
        }
    }

    /**
     * 检查依赖并显示提示
     */
    checkAndShowDependencyWarning(dependencies) {
        const missing = dependencies.filter(dep => typeof window[dep] === 'undefined');

        if (missing.length > 0) {
            this.showError(`缺少依赖: ${missing.join(', ')}，部分功能可能无法使用`);
            return false;
        }

        return true;
    }

    /**
     * 获取元素引用
     */
    getElement(id) {
        return this.elements[id] || document.getElementById(id);
    }

    /**
     * 添加动画效果
     */
    animateElement(element, animationClass) {
        if (!element || !animationClass) return;

        element.classList.add(animationClass);
        element.addEventListener('animationend', () => {
            element.classList.remove(animationClass);
        }, { once: true });
    }
}

// 导出UI管理器
export default UIManager;