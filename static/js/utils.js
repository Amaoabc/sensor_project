// static/js/utils.js
/**
 * 工具函数模块 - 包含通用工具函数
 */

class Utils {
    /**
     * 防抖函数
     */
    static debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    /**
     * 延迟函数
     */
    static sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    /**
     * 格式化时间显示
     */
    static formatTime(date) {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        const hours = String(date.getHours()).padStart(2, '0');
        const minutes = String(date.getMinutes()).padStart(2, '0');
        const seconds = String(date.getSeconds()).padStart(2, '0');
        
        return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
    }

    /**
     * 检查依赖是否加载
     */
    static checkDependencies(dependencies) {
        const missing = [];
        
        dependencies.forEach(dep => {
            if (typeof window[dep] === 'undefined') {
                missing.push(dep);
            }
        });
        
        if (missing.length > 0) {
            console.warn(`缺少依赖: ${missing.join(', ')}`);
            return false;
        }
        
        return true;
    }

    /**
     * 安全的JSON解析
     */
    static safeJsonParse(jsonString, defaultValue = {}) {
        try {
            return JSON.parse(jsonString);
        } catch (error) {
            console.warn('JSON解析失败:', error);
            return defaultValue;
        }
    }

    /**
     * 数值范围限制
     */
    static clamp(value, min, max) {
        return Math.min(Math.max(value, min), max);
    }

    /**
     * 生成随机ID
     */
    static generateId(length = 8) {
        return Math.random().toString(36).substr(2, length);
    }

    /**
     * 格式化文件大小
     */
    static formatFileSize(bytes) {
        if (bytes === 0) return '0 B';
        
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
}

// 导出工具类
export default Utils;