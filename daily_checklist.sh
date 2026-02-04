#!/bin/bash
# 传感器项目每日工作检查清单

echo "========================================"
echo "   传感器项目每日Git工作流程检查"
echo "========================================"
echo ""

# 1. 检查当前目录
echo "1. 📁 项目目录检查..."
if [ ! -d ~/sensor_project ]; then
    echo "   ❌ 错误：项目目录不存在"
    exit 1
fi
cd ~/sensor_project
echo "   ✅ 项目目录: $(pwd)"

# 2. 检查Git状态
echo ""
echo "2. 🔍 Git状态检查..."
git status --short

# 3. 检查远程更新
echo ""
echo "3. 📡 远程更新检查..."
git fetch --dry-run

# 4. 检查分支状态
echo ""
echo "4. 🌿 分支状态检查..."
git branch -vv

# 5. 建议操作
echo ""
echo "5. 📋 建议操作顺序："
echo "   a. 如果有未提交的更改："
echo "      1. 在VSCode中打开「源代码管理」面板"
echo "      2. 输入提交信息"
echo "      3. 点击「提交」按钮"
echo "   b. 如果有远程更新："
echo "      1. 点击「...」菜单"
echo "      2. 选择「拉取」"
echo "      3. 如有冲突，解决冲突"
echo "   c. 推送本地更改："
echo "      1. 点击「...」菜单"
echo "      2. 选择「推送」"
echo ""
echo "========================================"
echo "   重要：所有操作请在VSCode中完成！"
echo "========================================"