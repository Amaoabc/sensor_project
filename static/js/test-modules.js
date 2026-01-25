// static/js/test-modules.js
import Utils from './utils.js';
import SensorService from './sensor-service.js';
import ChartManager from './chart-manager.js';
import UIManager from './ui-manager.js';

console.log('模块导入测试开始...');

// 测试Utils模块
console.log('Utils模块:', Utils);
console.log('防抖函数:', Utils.debounce);
console.log('延迟函数:', Utils.sleep);

// 测试SensorService模块
const sensorService = new SensorService();
console.log('SensorService模块:', sensorService);

// 测试ChartManager模块
const chartManager = new ChartManager();
console.log('ChartManager模块:', chartManager);

// 测试UIManager模块
const uiManager = new UIManager();
console.log('UIManager模块:', uiManager);

console.log('模块导入测试完成！');