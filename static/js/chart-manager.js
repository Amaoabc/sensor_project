/**
 * 图表管理模块 - 处理所有图表操作（优化版）
 */

class ChartManager {
    constructor(config = {}) {
        this.config = {
            chartRanges: {
                fixed: {
                    temperature: { min: 5, max: 40 },
                    humidity: { min: 10, max: 90 },
                    co2: { min: 400, max: 1600 },
                    voc: { min: 0, max: 500 },      // 新增
                    nox: { min: 0, max: 500 }       // 新增
                },
                adaptive: true // 新增：是否启用自适应范围
            },
            ...config
        };

        this.charts = {
            co2: null,
            tempHumi: null,
            vocNox: null  // 新增
        };

        this.currentHours = {
            co2: 24,
            tempHumi: 24,
            vocNox: 24    // 新增
        };

        // 新增：图表颜色配置
        this.chartColors = {
            co2: {
                line: 'rgb(76, 201, 240)',
                fill: 'rgba(76, 201, 240, 0.15)',
                point: 'rgb(76, 201, 240)',
                gradient: {
                    start: 'rgba(76, 201, 240, 0.8)',
                    end: 'rgba(76, 201, 240, 0.1)'
                }
            },
            temperature: {
                line: 'rgb(247, 37, 133)',
                fill: 'rgba(247, 37, 133, 0.15)',
                point: 'rgb(247, 37, 133)',
                gradient: {
                    start: 'rgba(247, 37, 133, 0.8)',
                    end: 'rgba(247, 37, 133, 0.1)'
                }
            },
            humidity: {
                line: 'rgb(74, 214, 109)',
                fill: 'rgba(74, 214, 109, 0.15)',
                point: 'rgb(74, 214, 109)',
                gradient: {
                    start: 'rgba(74, 214, 109, 0.8)',
                    end: 'rgba(74, 214, 109, 0.1)'
                }
            },
            voc: {
                line: 'rgb(255, 159, 64)',
                fill: 'rgba(255, 159, 64, 0.15)',
                point: 'rgb(255, 159, 64)',
                gradient: {
                    start: 'rgba(255, 159, 64, 0.8)',
                    end: 'rgba(255, 159, 64, 0.1)'
                }
            },
            nox: {
                line: 'rgb(75, 192, 192)',
                fill: 'rgba(75, 192, 192, 0.15)',
                point: 'rgb(75, 192, 192)',
                gradient: {
                    start: 'rgba(75, 192, 192, 0.8)',
                    end: 'rgba(75, 192, 192, 0.1)'
                }
            }

        };
    }

    /**
     * 检查Chart.js是否可用
     */
    isChartAvailable() {
        return typeof Chart !== 'undefined';
    }

    /**
     * 初始化所有图表
     */
    initAllCharts() {
        if (!this.isChartAvailable()) {
            console.warn('Chart.js未加载，图表功能已禁用');
            return false;
        }

        try {
            this.initCo2Chart();
            this.initTempHumiChart();
            this.initVocNoxChart();  // 新增
            console.log('图表初始化完成');
            return true;
        } catch (error) {
            console.error('图表初始化失败:', error);
            return false;
        }
    }

    /**
     * 初始化CO2图表 - 优化版本
     */
    initCo2Chart() {
        const canvas = document.getElementById('co2Chart');
        if (!canvas) {
            console.error('找不到CO2图表canvas元素');
            return;
        }

        const existingChart = Chart.getChart(canvas);
        if (existingChart) {
            existingChart.destroy();
        }

        const ctx = canvas.getContext('2d');
        
        this.charts.co2 = new Chart(ctx, {
            type: 'line',
            data: {
                datasets: [{
                    label: 'CO₂浓度',
                    data: [],
                    borderColor: this.chartColors.co2.line,
                    backgroundColor: this.chartColors.co2.fill,
                    borderWidth: 2,
                    tension: 0.3,
                    fill: true,
                    pointRadius: 0,
                    pointHoverRadius: 6,
                    pointBackgroundColor: this.chartColors.co2.point,
                    pointBorderColor: 'rgba(255, 255, 255, 0.9)',
                    pointBorderWidth: 2
                }]
            },
            options: this.getChartOptions('co2'),
            plugins: [{
                beforeDraw: (chart) => {
                    const ctx = chart.ctx;
                    const chartArea = chart.chartArea;
                    
                    // 创建渐变背景
                    const gradient = this.createGradient(
                        ctx, 
                        chartArea, 
                        this.chartColors.co2
                    );
                    
                    chart.data.datasets[0].backgroundColor = gradient;
                }
            }]
        });
    }

    /**
     * 初始化温湿度图表 - 优化版本
     */
    initTempHumiChart() {
        const canvas = document.getElementById('tempHumiChart');
        if (!canvas) {
            console.error('找不到温湿度图表canvas元素');
            return;
        }

        const existingChart = Chart.getChart(canvas);
        if (existingChart) {
            existingChart.destroy();
        }

        const ctx = canvas.getContext('2d');
        
        this.charts.tempHumi = new Chart(ctx, {
            type: 'line',
            data: {
                datasets: [
                    {
                        label: '温度',
                        data: [],
                        borderColor: this.chartColors.temperature.line,
                        backgroundColor: this.chartColors.temperature.fill,
                        borderWidth: 2,
                        tension: 0.3,
                        fill: true,
                        pointRadius: 0,
                        pointHoverRadius: 6,
                        pointBackgroundColor: this.chartColors.temperature.point,
                        pointBorderColor: 'rgba(255, 255, 255, 0.9)',
                        pointBorderWidth: 2,
                        yAxisID: 'y'
                    },
                    {
                        label: '湿度',
                        data: [],
                        borderColor: this.chartColors.humidity.line,
                        backgroundColor: this.chartColors.humidity.fill,
                        borderWidth: 2,
                        tension: 0.3,
                        fill: true,
                        pointRadius: 0,
                        pointHoverRadius: 6,
                        pointBackgroundColor: this.chartColors.humidity.point,
                        pointBorderColor: 'rgba(255, 255, 255, 0.9)',
                        pointBorderWidth: 2,
                        yAxisID: 'y1'
                    }
                ]
            },
            options: this.getChartOptions('tempHumi'),
            plugins: [{
                beforeDraw: (chart) => {
                    const ctx = chart.ctx;
                    const chartArea = chart.chartArea;
                    
                    // 为温度线创建渐变背景
                    const tempGradient = this.createGradient(
                        ctx, 
                        chartArea, 
                        this.chartColors.temperature
                    );
                    
                    // 为湿度线创建渐变背景
                    const humiGradient = this.createGradient(
                        ctx, 
                        chartArea, 
                        this.chartColors.humidity
                    );
                    
                    chart.data.datasets[0].backgroundColor = tempGradient;
                    chart.data.datasets[1].backgroundColor = humiGradient;
                }
            }]
        });
    }
 
    /**
     * 初始化VOC/NOx图表
     */
    initVocNoxChart() {
        const canvas = document.getElementById('vocNoxChart');
        if (!canvas) {
            console.error('找不到VOC/NOx图表canvas元素');
            return;
        }

        const existingChart = Chart.getChart(canvas);
        if (existingChart) {
            existingChart.destroy();
        }

        const ctx = canvas.getContext('2d');
        
        this.charts.vocNox = new Chart(ctx, {
            type: 'line',
            data: {
                datasets: [
                    {
                        label: 'VOC指数',
                        data: [],
                        borderColor: this.chartColors.voc.line,
                        backgroundColor: this.chartColors.voc.fill,
                        borderWidth: 2,
                        tension: 0.3,
                        fill: true,
                        pointRadius: 0,
                        pointHoverRadius: 6,
                        pointBackgroundColor: this.chartColors.voc.point,
                        pointBorderColor: 'rgba(255, 255, 255, 0.9)',
                        pointBorderWidth: 2
                    },
                    {
                        label: 'NOx指数',
                        data: [],
                        borderColor: this.chartColors.nox.line,
                        backgroundColor: this.chartColors.nox.fill,
                        borderWidth: 2,
                        tension: 0.3,
                        fill: true,
                        pointRadius: 0,
                        pointHoverRadius: 6,
                        pointBackgroundColor: this.chartColors.nox.point,
                        pointBorderColor: 'rgba(255, 255, 255, 0.9)',
                        pointBorderWidth: 2
                    }
                ]
            },
            options: this.getChartOptions('vocNox'),
            plugins: [{
                beforeDraw: (chart) => {
                    const ctx = chart.ctx;
                    const chartArea = chart.chartArea;
                    
                    // 为VOC线创建渐变背景
                    const vocGradient = this.createGradient(
                        ctx, 
                        chartArea, 
                        this.chartColors.voc
                    );
                    
                    // 为NOx线创建渐变背景
                    const noxGradient = this.createGradient(
                        ctx, 
                        chartArea, 
                        this.chartColors.nox
                    );
                    
                    chart.data.datasets[0].backgroundColor = vocGradient;
                    chart.data.datasets[1].backgroundColor = noxGradient;
                }
            }]
        });
    }

    /**
     * 获取图表配置选项 - 优化版本
     */
    getChartOptions(type) {
        const hours = this.currentHours[type] || 24;
        const isMobile = window.innerWidth < 768;
        
        const baseOptions = {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        color: 'rgba(255, 255, 255, 0.9)',
                        padding: 15,
                        font: {
                            size: isMobile ? 12 : 14,
                            family: "'Segoe UI', 'Helvetica Neue', Arial"
                        },
                        boxWidth: 12,
                        boxHeight: 12,
                        usePointStyle: true
                    }
                },
                tooltip: {
                    enabled: true,
                    mode: 'index',
                    intersect: false,
                    backgroundColor: 'rgba(0, 0, 0, 0.85)',
                    titleColor: 'rgb(255, 255, 255)',
                    bodyColor: 'rgb(255, 255, 255)',
                    titleFont: {
                        size: 12,
                        weight: 'normal'
                    },
                    bodyFont: {
                        size: 13,
                        weight: 'bold'
                    },
                    padding: {
                        top: 10,
                        right: 12,
                        bottom: 10,
                        left: 12
                    },
                    cornerRadius: 6,
                    borderWidth: 0,
                    boxPadding: 6,
                    caretSize: 6,
                    displayColors: true,
                    callbacks: {
                        title: (tooltipItems) => {
                            if (tooltipItems.length > 0) {
                                const date = new Date(tooltipItems[0].parsed.x);
                                return date.toLocaleTimeString('zh-CN', {
                                    year: hours > 24 ? 'numeric' : undefined,
                                    month: '2-digit',
                                    day: '2-digit',
                                    hour: '2-digit',
                                    minute: '2-digit',
                                    second: '2-digit'
                                });
                            }
                            return '';
                        },
                        label: (context) => {
                            const label = context.dataset.label || '';
                            const value = context.parsed.y;
                            
                            if (type === 'co2') {
                                return `${label}: ${value.toFixed(0)} ppm`;
                            } else if (type === 'tempHumi') {
                                if (context.dataset.label === '温度') {
                                    return `${label}: ${value.toFixed(1)}°C`;
                                } else {
                                    return `${label}: ${value.toFixed(1)}%`;
                                }
                            }
                            return `${label}: ${value}`;
                        }
                    }
                }
            },
            animation: {
                duration: 600,
                easing: 'easeOutQuart'
            },
            transitions: {
                active: {
                    animation: {
                        duration: 300
                    }
                }
            },
            elements: {
                line: {
                    tension: 0.3, // 稍微减少曲线张力，使曲线更自然
                    borderWidth: 2,
                    borderCapStyle: 'round',
                    borderJoinStyle: 'round'
                },
                point: {
                    radius: 0, // 默认隐藏点，hover时显示
                    hoverRadius: 6,
                    hoverBorderWidth: 2,
                    backgroundColor: 'rgba(255, 255, 255, 0.9)'
                }
            }
        };

        // X轴配置
        const scales = {
            x: {
                type: 'time',
                time: {
                    tooltipFormat: 'yyyy-MM-dd HH:mm:ss',
                    unit: this.getTimeUnit(hours),
                    displayFormats: this.getDisplayFormats(hours),
                    round: 'minute'
                },
                grid: {
                    color: 'rgba(255, 255, 255, 0.1)',
                    lineWidth: 1,
                    drawBorder: false,
                    drawTicks: false
                },
                ticks: {
                    color: 'rgba(255, 255, 255, 0.6)',
                    maxRotation: 45,
                    minRotation: 0,
                    maxTicksLimit: isMobile ? 6 : 10,
                    font: {
                        size: isMobile ? 10 : 12
                    },
                    padding: 8
                },
                title: {
                    display: !isMobile,
                    text: '时间',
                    color: 'rgba(255, 255, 255, 0.8)',
                    font: {
                        size: 12,
                        weight: 'normal'
                    },
                    padding: { top: 10, bottom: 5 }
                },
                border: {
                    display: false
                }
            }
        };

        // Y轴配置
        if (type === 'co2') {
            scales.y = {
                type: 'linear',
                display: true,
                position: 'left',
                grid: {
                    color: 'rgba(255, 255, 255, 0.08)',
                    lineWidth: 1,
                    drawBorder: false,
                    drawTicks: false
                },
                ticks: {
                    color: 'rgba(255, 255, 255, 0.6)',
                    font: {
                        size: isMobile ? 10 : 12
                    },
                    padding: 6,
                    callback: function (value) {
                        return value + ' ppm';
                    }
                },
                title: {
                    display: !isMobile,
                    text: 'CO₂浓度 (ppm)',
                    color: 'rgba(255, 255, 255, 0.8)',
                    font: {
                        size: 12,
                        weight: 'normal'
                    },
                    padding: { top: 5, bottom: 10 }
                },
                border: {
                    display: false
                }
            };
        } 
        else if (type === 'tempHumi') {
            scales.y = {
                type: 'linear',
                display: true,
                position: 'left',
                grid: {
                    color: 'rgba(255, 255, 255, 0.08)',
                    lineWidth: 1,
                    drawBorder: false,
                    drawTicks: false
                },
                ticks: {
                    color: 'rgba(255, 255, 255, 0.6)',
                    font: {
                        size: isMobile ? 10 : 12
                    },
                    padding: 6,
                    callback: function (value) {
                        return value + '°C';
                    }
                },
                title: {
                    display: !isMobile,
                    text: '温度 (°C)',
                    color: 'rgba(255, 255, 255, 0.8)',
                    font: {
                        size: 12,
                        weight: 'normal'
                    },
                    padding: { top: 5, bottom: 10 }
                },
                border: {
                    display: false
                }
            };

            scales.y1 = {
                type: 'linear',
                display: true,
                position: 'right',
                grid: {
                    drawOnChartArea: false
                },
                ticks: {
                    color: 'rgba(255, 255, 255, 0.6)',
                    font: {
                        size: isMobile ? 10 : 12
                    },
                    padding: 6,
                    callback: function (value) {
                        return value + '%';
                    }
                },
                title: {
                    display: !isMobile,
                    text: '湿度 (%)',
                    color: 'rgba(255, 255, 255, 0.8)',
                    font: {
                        size: 12,
                        weight: 'normal'
                    },
                    padding: { top: 5, bottom: 10 }
                },
                border: {
                    display: false
                }
            };
        }
        // 扩展Y轴配置
        else if (type === 'vocNox') {
            scales.y = {
                type: 'linear',
                display: true,
                position: 'left',
                grid: {
                    color: 'rgba(255, 255, 255, 0.08)',
                    lineWidth: 1,
                    drawBorder: false,
                    drawTicks: false
                },
                ticks: {
                    color: 'rgba(255, 255, 255, 0.6)',
                    font: {
                        size: isMobile ? 10 : 12
                    },
                    padding: 6,
                    callback: function (value) {
                        return value + ' index';
                    }
                },
                title: {
                    display: !isMobile,
                    text: 'VOC/NOx指数',
                    color: 'rgba(255, 255, 255, 0.8)',
                    font: {
                        size: 12,
                        weight: 'normal'
                    },
                    padding: { top: 5, bottom: 10 }
                },
                border: {
                    display: false
                }
            };
        }

        // 如果是自适应范围，不设置固定min/max
        if (!this.config.adaptive) {
            if (type === 'co2') {
                scales.y.min = this.config.chartRanges.fixed.co2.min;
                scales.y.max = this.config.chartRanges.fixed.co2.max;
            } else if (type === 'tempHumi') {
                scales.y.min = this.config.chartRanges.fixed.temperature.min;
                scales.y.max = this.config.chartRanges.fixed.temperature.max;
                scales.y1.min = this.config.chartRanges.fixed.humidity.min;
                scales.y1.max = this.config.chartRanges.fixed.humidity.max;
            }
            else if (type === 'vocNox') {
                scales.y.min = this.config.chartRanges.fixed.voc.min;
                scales.y.max = this.config.chartRanges.fixed.voc.max;
            }

        baseOptions.scales = scales;
        return baseOptions;
        }
    }

    /**
     * 根据小时数获取时间单位
     */
    getTimeUnit(hours) {
        if (hours <= 1) return 'minute';
        if (hours <= 6) return 'hour';
        if (hours <= 24) return 'hour';
        if (hours <= 168) return 'day';
        return 'day';
    }

    /**
     * 根据小时数获取显示格式
     */
    getDisplayFormats(hours) {
        if (hours <= 1) {
            return {
                minute: 'HH:mm',
                hour: 'HH:mm'
            };
        } else if (hours <= 6) {
            return {
                hour: 'HH:mm',
                day: 'MM-dd'
            };
        } else if (hours <= 24) {
            return {
                hour: 'HH:mm',
                day: 'MM-dd'
            };
        } else {
            return {
                day: 'MM-dd',
                week: 'MM-dd',
                month: 'yyyy-MM'
            };
        }
    }

    /**
     * 创建渐变背景
     */
    createGradient(ctx, chartArea, colorConfig) {
        const gradient = ctx.createLinearGradient(
            0, chartArea.top,
            0, chartArea.bottom
        );
        
        gradient.addColorStop(0, colorConfig.gradient.start);
        gradient.addColorStop(1, colorConfig.gradient.end);
        
        return gradient;
    }

    /**
     * 转换数据为时间轴格式
     */
    convertToTimeSeriesData(data, hours) {
        if (!data.labels || !Array.isArray(data.labels)) {
            return data;
        }

        const result = {
            datasets: []
        };

        const now = new Date();

        // 转换标签为时间戳
        const timeLabels = data.labels.map((label, index) => {
            try {
                if (hours <= 24) {
                    // 格式: "HH:mm"
                    const [hoursStr, minutesStr] = label.split(':');
                    const date = new Date(now);
                    date.setHours(parseInt(hoursStr), parseInt(minutesStr), 0, 0);

                    if (date > now) {
                        date.setDate(date.getDate() - 1);
                    }

                    return date;
                } else {
                    // 格式: "MM-DD HH:mm"
                    const [dateStr, timeStr] = label.split(' ');
                    const [monthStr, dayStr] = dateStr.split('-');
                    const [hoursStr, minutesStr] = timeStr.split(':');

                    const date = new Date(now.getFullYear(),
                        parseInt(monthStr) - 1,
                        parseInt(dayStr),
                        parseInt(hoursStr),
                        parseInt(minutesStr), 0, 0);

                    return date;
                }
            } catch (error) {
                console.warn('时间标签解析失败:', error, label);
                const offset = (data.labels.length - index - 1) * (hours * 3600000 / data.labels.length);
                return new Date(now.getTime() - offset);
            }
        });

        // 转换数据集
        if (data.datasets && Array.isArray(data.datasets)) {
            result.datasets = data.datasets.map((dataset, datasetIndex) => {
                const timeSeriesData = [];

                for (let i = 0; i < Math.min(timeLabels.length, dataset.data.length); i++) {
                    timeSeriesData.push({
                        x: timeLabels[i],
                        y: dataset.data[i]
                    });
                }

                return {
                    ...dataset,
                    data: timeSeriesData
                };
            });
        }

        return result;
    }

    /**
     * 更新图表数据 - 优化版本
     */
    updateChart(chartType, apiData) {
        const chart = this.charts[chartType];
        if (!chart) {
            console.error(`找不到图表: ${chartType}`);
            return;
        }

        if (!apiData.success) {
            console.warn(`图表${chartType}数据获取失败`);
            return;
        }

        // 转换为时间序列数据
        const timeSeriesData = this.convertToTimeSeriesData(
            apiData.data,
            this.currentHours[chartType]
        );

        // 更新图表数据
        chart.data = timeSeriesData;
        
        // 计算并设置自适应范围
        if (this.config.adaptive) {
            this.adjustYAxisRange(chart, chartType, timeSeriesData);
        }
        
        // 平滑更新
        chart.update('none');

        // 返回统计信息
        return this.getChartStats(chartType, apiData.data);
    }

    /**
     * 自适应调整Y轴范围
     */
    adjustYAxisRange(chart, chartType, data) {
        if (chartType === 'co2') {
            const values = data.datasets[0].data.map(item => item.y);
            const validValues = values.filter(v => !isNaN(v) && v !== null);
            
            if (validValues.length > 0) {
                const min = Math.min(...validValues);
                const max = Math.max(...validValues);
                const range = max - min;
                
                // 添加10%的padding
                chart.options.scales.y.min = Math.max(300, min - range * 0.1);
                chart.options.scales.y.max = Math.min(5000, max + range * 0.1);
            }
        } else if (chartType === 'tempHumi') {
            // 处理温度
            const tempValues = data.datasets[0]?.data.map(item => item.y) || [];
            const validTempValues = tempValues.filter(v => !isNaN(v) && v !== null);
            
            if (validTempValues.length > 0) {
                const tempMin = Math.min(...validTempValues);
                const tempMax = Math.max(...validTempValues);
                const tempRange = tempMax - tempMin;
                
                chart.options.scales.y.min = Math.max(-10, tempMin - tempRange * 0.1);
                chart.options.scales.y.max = Math.min(60, tempMax + tempRange * 0.1);
            }
            else if (chartType === 'vocNox') {
                // 处理VOC数据
                const vocValues = data.datasets[0]?.data.map(item => item.y) || [];
                const validVocValues = vocValues.filter(v => !isNaN(v) && v !== null);
                
                if (validVocValues.length > 0) {
                    const vocMin = Math.min(...validVocValues);
                    const vocMax = Math.max(...validVocValues);
                    const vocRange = vocMax - vocMin;
                    
                    chart.options.scales.y.min = Math.max(0, vocMin - vocRange * 0.1);
                    chart.options.scales.y.max = Math.min(500, vocMax + vocRange * 0.1);
                }
            }
            
            // 处理湿度
            const humiValues = data.datasets[1]?.data.map(item => item.y) || [];
            const validHumiValues = humiValues.filter(v => !isNaN(v) && v !== null);
            
            if (validHumiValues.length > 0) {
                const humiMin = Math.min(...validHumiValues);
                const humiMax = Math.max(...validHumiValues);
                const humiRange = humiMax - humiMin;
                
                chart.options.scales.y1.min = Math.max(0, humiMin - humiRange * 0.1);
                chart.options.scales.y1.max = Math.min(100, humiMax + humiRange * 0.1);
            }
        }
    }

    /**
     * 获取图表统计信息
     */
    getChartStats(chartType, chartData) {
        // 处理CO2图表
        if (chartType === 'co2') {
            // 统一获取数据数组
            let dataArray = [];

            if (Array.isArray(chartData)) {
                // 如果chartData直接就是数组
                dataArray = chartData;
            } else if (chartData && chartData.datasets) {
                // 如果chartData是Chart.js格式的数据
                dataArray = chartData.datasets[0]?.data || [];
            }

            // 过滤掉无效数据（null, undefined, NaN）
            const validData = dataArray.filter(value =>
                value !== null &&
                value !== undefined &&
                !isNaN(value)
            );

            if (validData.length === 0) {
                return null;
            }

            // 统一计算统计信息
            const stats = {
                min: Math.min(...validData),
                max: Math.max(...validData),
                avg: validData.reduce((sum, val) => sum + val, 0) / validData.length
            };

            return stats;
        }
        // 处理温湿度图表
        else if (chartType === 'tempHumi') {
            // 确保数据格式正确
            if (!chartData || !chartData.datasets || !Array.isArray(chartData.datasets)) {
                return null;
            }

            // 分别获取温度和湿度数据
            const tempDataset = chartData.datasets.find(dataset => dataset.label === '温度');
            const humiDataset = chartData.datasets.find(dataset => dataset.label === '湿度');

            const tempData = tempDataset?.data || [];
            const humiData = humiDataset?.data || [];

            // 过滤无效数据
            const validTempData = tempData.filter(value =>
                value !== null && value !== undefined && !isNaN(value)
            );
            const validHumiData = humiData.filter(value =>
                value !== null && value !== undefined && !isNaN(value)
            );

            // 计算统计信息
            const tempStats = validTempData.length > 0 ? {
                min: Math.min(...validTempData),
                max: Math.max(...validTempData),
                avg: validTempData.reduce((sum, val) => sum + val, 0) / validTempData.length
            } : null;

            const humiStats = validHumiData.length > 0 ? {
                min: Math.min(...validHumiData),
                max: Math.max(...validHumiData),
                avg: validHumiData.reduce((sum, val) => sum + val, 0) / validHumiData.length
            } : null;

            // 返回包含温度和湿度统计的对象
            return {
                temperature: tempStats,
                humidity: humiStats
            };
        }
        else if (chartType === 'vocNox') {
            // 统一获取数据数组
            let vocData = [];
            let noxData = [];

            if (chartData && chartData.datasets) {
                // 获取VOC和NOx数据集
                vocData = chartData.datasets[0]?.data || [];
                noxData = chartData.datasets[1]?.data || [];
            }

            // 过滤掉无效数据
            const validVocData = vocData.filter(value =>
                value !== null && value !== undefined && !isNaN(value)
            );
            const validNoxData = noxData.filter(value =>
                value !== null && value !== undefined && !isNaN(value)
            );

            // 计算统计信息
            const vocStats = validVocData.length > 0 ? {
                min: Math.min(...validVocData),
                max: Math.max(...validVocData),
                avg: validVocData.reduce((sum, val) => sum + val, 0) / validVocData.length
            } : null;

            const noxStats = validNoxData.length > 0 ? {
                min: Math.min(...validNoxData),
                max: Math.max(...validNoxData),
                avg: validNoxData.reduce((sum, val) => sum + val, 0) / validNoxData.length
            } : null;

            return {
                voc: vocStats,
                nox: noxStats
            };
        }
        return null;
    }

    /**
     * 设置图表时间范围
     */
    setChartHours(chartType, hours) {
        this.currentHours[chartType] = hours;
        console.log(`设置${chartType}图表时间范围为${hours}小时`);
    }

    /**
     * 调整图表大小
     */
    resizeCharts() {
        if (this.charts.co2) this.charts.co2.resize();
        if (this.charts.tempHumi) this.charts.tempHumi.resize();
        if (this.charts.vocNox) this.charts.vocNox.resize();  // 新增
    }

    /**
     * 销毁所有图表
     */
    destroyCharts() {
        if (this.charts.co2) {
            this.charts.co2.destroy();
            this.charts.co2 = null;
        }

        if (this.charts.tempHumi) {
            this.charts.tempHumi.destroy();
            this.charts.tempHumi = null;
        }

        if (this.charts.vocNox) {
            this.charts.vocNox.destroy();
            this.charts.vocNox = null;
        }

        console.log('图表已销毁');
    }

    /**
     * 获取图表状态
     */
    getChartStatus() {
        return {
            co2: {
                initialized: this.charts.co2 !== null,
                currentHours: this.currentHours.co2
            },
            tempHumi: {
                initialized: this.charts.tempHumi !== null,
                currentHours: this.currentHours.tempHumi
            },
            vocNox: {
                initialized: this.charts.vocNox !== null,
                currentHours: this.currentHours.vocNox
            }
        };
    }
}

// 导出图表管理器
export default ChartManager;